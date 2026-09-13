import asyncio                                    as AsyncIOBuiltin
import datetime                                   as DateTime
import json                                       as JSONParser
import re                                         as RegularExpressions
import time                                       as TimeLibrary
import typing                                     as Typing
import httpx2                                     as HTTPClient
import sqlalchemy                                 as SQLAlchemy
import sqlalchemy.ext.asyncio                     as AsyncIO
import Server.Config                              as Config
import Server.Models.Character                    as Character
import Server.Models.DND5ECharacterSchema         as CharacterSchema
import Server.Models.Mail                         as Mail
import Server.Models.StorageFile                  as StorageFile
import Server.Models.User                         as User
import Server.Services.CharacterMappingService    as CharacterMapping
import Server.Services.DebugService               as Debug
import Server.Services.ImageProcessingService     as ImageProcessing
import Server.Services.MailboxService             as Mailbox
import Server.Services.OracleStorageService       as OracleStorage

DICECLOUD_V1_URL_PATTERN: RegularExpressions.Pattern = RegularExpressions.compile(r"^(?:https?:\/\/)?v1\.dicecloud\.com\/character\/([a-zA-Z0-9_-]+)(?:[\/?#].*)?$", RegularExpressions.IGNORECASE)
DICECLOUD_V2_URL_PATTERN: RegularExpressions.Pattern = RegularExpressions.compile(r"^(?:https?:\/\/)?(?!v1\.)(?:(?:beta|app|www)\.)?dicecloud\.com\/character\/([a-zA-Z0-9_-]+)(?:[\/?#].*)?$", RegularExpressions.IGNORECASE)
DDB_URL_PATTERN         : RegularExpressions.Pattern = RegularExpressions.compile(r"^(?:https?:\/\/)?(?:www\.)?dndbeyond\.com\/(?:profile\/[^\/]+\/)?characters\/(\d+)(?:[\/?#].*)?$", RegularExpressions.IGNORECASE)
DDB_SHORT_PATTERN       : RegularExpressions.Pattern = RegularExpressions.compile(r"^(?:https?:\/\/)?ddb\.ac\/(?:characters\/)?(\d+)(?:[\/?#].*)?$", RegularExpressions.IGNORECASE)
DDB_PDF_PATTERN         : RegularExpressions.Pattern = RegularExpressions.compile(r"^(?:https?:\/\/)?(?:www\.)?dndbeyond\.com\/sheet-pdfs\/.*?[_-]?(\d+)\.pdf(?:[\/?#].*)?$", RegularExpressions.IGNORECASE)
DDB_SVC_PATTERN         : RegularExpressions.Pattern = RegularExpressions.compile(r"^(?:https?:\/\/)?character-service\.dndbeyond\.com\/character\/v5\/character\/(\d+)(?:[\/?#].*)?$", RegularExpressions.IGNORECASE)

class CharacterImportService:
    def __init__(self) -> None:
        self.HTTPClientSession: Typing.Optional[HTTPClient.AsyncClient] = None
        self.DC2Token         : Typing.Optional[str]                    = None
        self.DC2Expiry        : float                                   = 0.0

    def GetHTTPClient(self) -> HTTPClient.AsyncClient:
        if ((self.HTTPClientSession is None) or self.HTTPClientSession.is_closed):
            ClientLimits: HTTPClient.Limits = HTTPClient.Limits(max_connections = 20, max_keepalive_connections = 10, keepalive_expiry = 30.0)
            self.HTTPClientSession = HTTPClient.AsyncClient(timeout = 30.0, limits = ClientLimits, follow_redirects = True)

        return self.HTTPClientSession

    async def CloseClient(self) -> None:
        if ((self.HTTPClientSession is not None) and (not self.HTTPClientSession.is_closed)):
            await self.HTTPClientSession.aclose()
            self.HTTPClientSession = None

    async def ExecuteRequestWithRetry(self, Method: str, TargetURL: str, Headers: Typing.Dict[str, str], RequestPayload: Typing.Optional[Typing.Dict[str, Typing.Any]] = None, MaxRetries: int = 3) -> HTTPClient.Response:
        ClientConnection: HTTPClient.AsyncClient = self.GetHTTPClient()
        AttemptIndex: int = 0
        while (AttemptIndex < MaxRetries):
            try:
                if (Method.upper() == "POST"):
                    Response = await ClientConnection.post(TargetURL, headers = Headers, json = RequestPayload)

                else:
                    Response = await ClientConnection.get(TargetURL, headers = Headers)

                if (Response.status_code == 429):
                    AttemptIndex += 1
                    WaitSeconds: float = 2.0 * AttemptIndex
                    try:
                        ResponseData = Response.json()
                        if (isinstance(ResponseData, dict) and ("timeToReset" in ResponseData)):
                            WaitSeconds = max(0.5, float(ResponseData["timeToReset"]) / 1000.0)

                        elif ("Retry-After" in Response.headers):
                            WaitSeconds = max(0.5, float(Response.headers["Retry-After"]))

                    except Exception:
                        pass

                    if (AttemptIndex < MaxRetries):
                        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Rate limited by external service. Backing off for {WaitSeconds:.2f}s (Attempt {AttemptIndex}/{MaxRetries})")
                        await AsyncIOBuiltin.sleep(WaitSeconds)
                        continue

                elif ((Response.status_code in (502, 503, 504)) and (AttemptIndex < (MaxRetries - 1))):
                    AttemptIndex += 1
                    await AsyncIOBuiltin.sleep(1.0 * AttemptIndex)
                    continue

                return Response

            except (HTTPClient.RequestError, HTTPClient.TimeoutException) as NetworkError:
                AttemptIndex += 1
                if (AttemptIndex >= MaxRetries):
                    raise NetworkError

                await AsyncIOBuiltin.sleep(1.0 * AttemptIndex)

        raise HTTPClient.RequestError(f"Request failed after {MaxRetries} retries: {TargetURL}")

    def DetectImportSource(self, TargetURL: str) -> Typing.Tuple[Typing.Optional[str], Typing.Optional[str], Typing.Optional[str]]:
        CleanedURL: str = TargetURL.strip()
        DC1Match = DICECLOUD_V1_URL_PATTERN.search(CleanedURL)
        if (DC1Match is not None):
            CharacterID: str = DC1Match.group(1)
            if (CharacterID.lower() != "json"):
                Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Detected Import Source: DC1 (ID=\"{CharacterID}\")")
                return ("DC1", CharacterID, "Dicecloud v1")

        DC2Match = DICECLOUD_V2_URL_PATTERN.search(CleanedURL)
        if (DC2Match is not None):
            CharacterID = DC2Match.group(1)
            Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Detected Import Source: DC2 (ID=\"{CharacterID}\")")
            return ("DC2", CharacterID, "Dicecloud v2")

        DDBCharMatch = DDB_URL_PATTERN.search(CleanedURL)
        if (DDBCharMatch is not None):
            CharacterID = DDBCharMatch.group(1)
            Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Detected Import Source: DDB (ID=\"{CharacterID}\")")
            return ("DDB", CharacterID, "D&D Beyond")

        DDBShortMatch = DDB_SHORT_PATTERN.search(CleanedURL)
        if (DDBShortMatch is not None):
            CharacterID = DDBShortMatch.group(1)
            Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Detected Import Source: DDB Shortlink (ID=\"{CharacterID}\")")
            return ("DDB", CharacterID, "D&D Beyond")

        DDBPDFMatch = DDB_PDF_PATTERN.search(CleanedURL)
        if (DDBPDFMatch is not None):
            CharacterID = DDBPDFMatch.group(1)
            Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Detected Import Source: DDB PDF (ID=\"{CharacterID}\")")
            return ("DDB", CharacterID, "D&D Beyond")

        DDBSvcMatch = DDB_SVC_PATTERN.search(CleanedURL)
        if (DDBSvcMatch is not None):
            CharacterID = DDBSvcMatch.group(1)
            Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Detected Import Source: DDB Service (ID=\"{CharacterID}\")")
            return ("DDB", CharacterID, "D&D Beyond")

        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Failed to Detect Import Source for URL: \"{CleanedURL[:20]}…\"")
        return (None, None, None)

    async def GetDC2AuthToken(self, ForceReauthenticate: bool = False) -> str:
        CurrentTimestamp: float = TimeLibrary.time()
        if ((not ForceReauthenticate) and (self.DC2Token is not None) and (CurrentTimestamp < self.DC2Expiry)):
            return self.DC2Token

        LoginURL: str = "https://dicecloud.com/api/login"
        LoginPayload: Typing.Dict[str, str] = {
            "username": Config.GLOBAL_SETTINGS.DICECLOUD_USERNAME.strip(),
            "password": Config.GLOBAL_SETTINGS.DICECLOUD_PASSWORD.strip()
        }
        Headers: Typing.Dict[str, str] = {
            "User-Agent"  : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) zibell/1.0",
            "Content-Type": "application/json",
            "Accept"      : "application/json"
        }
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = "Authenticating with Dicecloud v2 Service")
        try:
            Response = await self.ExecuteRequestWithRetry("POST", LoginURL, Headers, LoginPayload)

        except Exception as LoginException:
            Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Dicecloud v2 Login Connection Error: {type(LoginException).__name__}")
            raise ValueError(f"Failed to connect to Dicecloud v2 authentication service: {type(LoginException).__name__}")

        if ((Response.status_code == 401) or (Response.status_code == 403)):
            Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Dicecloud v2 Authentication Rejected: Status={Response.status_code}")
            raise ValueError("Dicecloud v2 login credentials were rejected. Please check DICECLOUD_USERNAME and DICECLOUD_PASSWORD in .env.")

        if (Response.status_code != 200):
            Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Dicecloud v2 Authentication Failed: Status={Response.status_code}")
            raise ValueError(f"Dicecloud v2 login failed with status code {Response.status_code}.")

        try:
            DataDictionary: Typing.Dict[str, Typing.Any] = Response.json()

        except Exception as ParsingError:
            raise ValueError("Failed to parse authentication response from Dicecloud v2.")

        Token: Typing.Optional[str] = DataDictionary.get("token")
        if ((not Token) or (len(Token) == 0)):
            raise ValueError("Dicecloud v2 login did not return a valid authentication token.")

        self.DC2Token = Token
        ExpiryString: Typing.Optional[str] = DataDictionary.get("tokenExpires")
        if ExpiryString:
            try:
                ParsedDate = DateTime.datetime.fromisoformat(ExpiryString.replace("Z", "+00:00"))
                self.DC2Expiry = ParsedDate.timestamp() - 60.0

            except Exception:
                self.DC2Expiry = CurrentTimestamp + 3600.0

        else:
            self.DC2Expiry = CurrentTimestamp + 3600.0

        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = "Dicecloud v2 Authentication Successful")
        return self.DC2Token

    async def DownloadAndStorePortrait(self, CurrentUser: User.User, PortraitURL: str, DatabaseSession: AsyncIO.AsyncSession) -> Typing.Optional[str]:
        if ((not PortraitURL) or (CurrentUser is None)):
            return None

        CleanedURL: str = PortraitURL.strip()
        if (len(CleanedURL) == 0):
            return None

        try:
            Headers: Typing.Dict[str, str] = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) zibell/1.0",
                "Accept"    : "image/jpeg,image/png,image/webp,image/*"
            }
            Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Downloading Character Portrait for User: \"{CurrentUser.ID[:8]}…\"")
            Response = await self.ExecuteRequestWithRetry("GET", CleanedURL, Headers)
            if (Response.status_code != 200):
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Portrait Download Failed: Status={Response.status_code}")
                return None

            RawBytes: bytes = Response.content
            if (len(RawBytes) == 0):
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Portrait Download Returned Empty Response")
                return None

            SanitizedBytes, ContentType = ImageProcessing.GLOBAL_IMAGE_PROCESSING_SERVICE.SanitizeAndOptimizeImage(RawBytes, "portrait.jpg")
            FileSizeBytes: int = len(SanitizedBytes)
            if not OracleStorage.GLOBAL_STORAGE_SERVICE.CheckQuotaAvailable(CurrentUser, FileSizeBytes):
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Portrait Storage Quota Exceeded for User: \"{CurrentUser.ID[:8]}…\"")
                return None

            OriginalFileName: str = "portrait.jpg"
            ObjectKey: Typing.Optional[str] = await OracleStorage.GLOBAL_STORAGE_SERVICE.UploadFile(CurrentUser, OriginalFileName, ContentType, SanitizedBytes)
            if not ObjectKey:
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = "Portrait Upload to Storage Provider Failed")
                return None

            NewStorageFile: StorageFile.StorageFile = StorageFile.StorageFile(OwnerID = CurrentUser.ID, FileName = OriginalFileName, ContentType = ContentType, FileSizeBytes = FileSizeBytes, ObjectKey = ObjectKey)
            DatabaseSession.add(NewStorageFile)
            CurrentUser.StorageUsedBytes += FileSizeBytes
            await DatabaseSession.commit()
            await DatabaseSession.refresh(NewStorageFile)
            Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Character Portrait Stored: FileID=\"{NewStorageFile.ID[:8]}…\", Size={FileSizeBytes}B")
            return NewStorageFile.ID

        except Exception as StorageError:
            Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Portrait Storage Error: {type(StorageError).__name__}")
            return None

    async def FetchCharacterData(self, SourceType: str, CharacterID: str) -> Typing.Dict[str, Typing.Any]:
        if (SourceType == "DC1"):
            APIKey: str = Config.GLOBAL_SETTINGS.DICECLOUD_API_KEY
            if (len(APIKey.strip()) == 0):
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Dicecloud v1 Import Aborted: API Key Unconfigured")
                raise ValueError("Dicecloud API key is not configured in .env. Please set DICECLOUD_API_KEY to import from Dicecloud v1.")

            RequestURL: str = f"https://v1.dicecloud.com/character/{CharacterID}/json?key={APIKey.strip()}"
            Headers: Typing.Dict[str, str] = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) zibell/1.0",
                "Accept"    : "application/json"
            }
            Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Fetching Dicecloud v1 Character: ID=\"{CharacterID}\"")
            try:
                Response = await self.ExecuteRequestWithRetry("GET", RequestURL, Headers)

            except (HTTPClient.RequestError, HTTPClient.TimeoutException) as NetworkError:
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Dicecloud v1 Connection Error: {type(NetworkError).__name__}")
                raise ValueError(f"Failed to connect to Dicecloud v1 service: {type(NetworkError).__name__}")

            if ((Response.status_code == 401) or (Response.status_code == 403)):
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Dicecloud v1 Authentication Failed: Status={Response.status_code}")
                raise ValueError("Dicecloud API key was rejected or unauthorized. Please verify your DICECLOUD_API_KEY in .env.")

            if (Response.status_code == 404):
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Dicecloud v1 Character Not Found: ID=\"{CharacterID}\"")
                raise ValueError(f"Character \"{CharacterID}\" not found on Dicecloud v1. Verify the URL and ensure the sheet is accessible.")

            if (Response.status_code != 200):
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Dicecloud v1 Request Failed: Status={Response.status_code}")
                raise ValueError(f"Failed to fetch character from Dicecloud v1 (HTTP {Response.status_code}).")

            try:
                ParsedData: Typing.Dict[str, Typing.Any] = Response.json()

            except Exception as ParsingError:
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Dicecloud v1 JSON Parse Error: {type(ParsingError).__name__}")
                raise ValueError("Received invalid or corrupted JSON data from Dicecloud v1.")

            if (isinstance(ParsedData, dict) and ("error" in ParsedData)):
                ErrorMessage: str = str(ParsedData["error"])
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Dicecloud v1 API Error: \"{ErrorMessage[:35]}\"")
                raise ValueError(f"Dicecloud v1 API error: {ErrorMessage}")

            return ParsedData

        if (SourceType == "DC2"):
            AuthToken: str = await self.GetDC2AuthToken()
            RequestURL: str = f"https://dicecloud.com/api/creature/{CharacterID}"
            Headers: Typing.Dict[str, str] = {
                "User-Agent"   : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) zibell/1.0",
                "Accept"       : "application/json",
                "Authorization": f"Bearer {AuthToken}"
            }
            Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Fetching Dicecloud v2 Character: ID=\"{CharacterID}\"")
            try:
                Response = await self.ExecuteRequestWithRetry("GET", RequestURL, Headers)

            except Exception as NetworkError:
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Dicecloud v2 Connection Error: {type(NetworkError).__name__}")
                raise ValueError(f"Failed to connect to Dicecloud v2 service: {type(NetworkError).__name__}")

            if ((Response.status_code == 401) or (Response.status_code == 403)):
                AuthToken = await self.GetDC2AuthToken(ForceReauthenticate = True)
                Headers["Authorization"] = f"Bearer {AuthToken}"
                Response = await self.ExecuteRequestWithRetry("GET", RequestURL, Headers)
                if ((Response.status_code == 401) or (Response.status_code == 403)):
                    Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Dicecloud v2 Access Forbidden: Status={Response.status_code}")
                    raise ValueError(f"Access forbidden by Dicecloud v2 for character \"{CharacterID}\". Ensure the character is shared with your account or made public.")

            if (Response.status_code == 404):
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Dicecloud v2 Character Not Found: ID=\"{CharacterID}\"")
                raise ValueError(f"Character \"{CharacterID}\" was not found on Dicecloud v2. Verify the URL.")

            if (Response.status_code != 200):
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Dicecloud v2 Request Failed: Status={Response.status_code}")
                raise ValueError(f"Failed to fetch character from Dicecloud v2 (HTTP {Response.status_code}).")

            try:
                ParsedData = Response.json()

            except Exception as ParsingError:
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Dicecloud v2 JSON Parse Error: {type(ParsingError).__name__}")
                raise ValueError("Received invalid or corrupted JSON data from Dicecloud v2.")

            return ParsedData

        if (SourceType == "DDB"):
            RequestURL: str = f"https://character-service.dndbeyond.com/character/v5/character/{CharacterID}"
            Headers: Typing.Dict[str, str] = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept"    : "application/json"
            }
            Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Fetching DDB Character: ID=\"{CharacterID}\"")
            try:
                Response = await self.ExecuteRequestWithRetry("GET", RequestURL, Headers)

            except (HTTPClient.RequestError, HTTPClient.TimeoutException) as NetworkError:
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"DDB Connection Error: {type(NetworkError).__name__}")
                raise ValueError(f"Failed to connect to D&D Beyond service: {type(NetworkError).__name__}")

            if (Response.status_code == 403):
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"DDB Access Forbidden: ID=\"{CharacterID}\"")
                raise ValueError(f"Access forbidden by D&D Beyond for character '{CharacterID}'. Please make sure the character sheet is set to Public.")

            if (Response.status_code == 404):
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"DDB Character Not Found: ID=\"{CharacterID}\"")
                raise ValueError(f"Character '{CharacterID}' was not found on D&D Beyond.")

            if (Response.status_code != 200):
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"DDB Request Failed: Status={Response.status_code}")
                raise ValueError(f"Failed to fetch character from D&D Beyond (HTTP {Response.status_code}).")

            try:
                ParsedData = Response.json()

            except Exception as ParsingError:
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"DDB JSON Parse Error: {type(ParsingError).__name__}")
                raise ValueError("Received invalid or corrupted JSON data from D&D Beyond.")

            if (isinstance(ParsedData, dict) and (ParsedData.get("success") is False)):
                ErrorMessage: str = str(ParsedData.get("message") or "Unknown error from D&D Beyond")
                Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"DDB API Error: \"{ErrorMessage[:35]}\"")
                raise ValueError(f"D&D Beyond error: {ErrorMessage}")

            return ParsedData

        raise ValueError(f"Unsupported import source: '{SourceType}'")

    async def ImportCharacterFromURL(self, TargetURL: str, OwnerID: str, DatabaseSession: AsyncIO.AsyncSession) -> Character.Character:
        SourceType, CharacterID, UtilityName = self.DetectImportSource(TargetURL)
        if ((SourceType is None) or (CharacterID is None)):
            raise ValueError("Unrecognized character sheet URL. Please provide a valid Dicecloud or D&D Beyond URL.")

        RawJSON: Typing.Dict[str, Typing.Any] = await self.FetchCharacterData(SourceType, CharacterID)
        if (SourceType == "DC1"):
            UnifiedSheet: CharacterSchema.DND5ECharacterSheet = CharacterMapping.GLOBAL_CHARACTER_MAPPER.MapDC1Character(RawJSON)

        elif (SourceType == "DC2"):
            UnifiedSheet = CharacterMapping.GLOBAL_CHARACTER_MAPPER.MapDC2Character(RawJSON)

        elif (SourceType == "DDB"):
            UnifiedSheet = CharacterMapping.GLOBAL_CHARACTER_MAPPER.MapDDBCharacter(RawJSON)

        else:
            UnifiedSheet = CharacterMapping.GLOBAL_CHARACTER_MAPPER.IngestUniversalCharacterData(RawJSON)

        UserQueryStatement = SQLAlchemy.select(User.User).where(User.User.ID == OwnerID)
        UserQueryResult    = await DatabaseSession.execute(UserQueryStatement)
        CurrentUser: Typing.Optional[User.User] = UserQueryResult.scalars().first()

        PortraitURL: Typing.Optional[str] = getattr(getattr(UnifiedSheet, "PhysicalAppearance", None), "PortraitURL", None)
        PortraitFileID: Typing.Optional[str] = None
        if ((PortraitURL is not None) and (CurrentUser is not None)):
            PortraitFileID = await self.DownloadAndStorePortrait(CurrentUser, PortraitURL, DatabaseSession)

        if ((PortraitFileID is not None) and (UnifiedSheet.PhysicalAppearance is not None)):
            UnifiedSheet.PhysicalAppearance.PortraitFileID = PortraitFileID

        Payload: Typing.Dict[str, Typing.Any] = CharacterMapping.GLOBAL_CHARACTER_MAPPER.ExportToDatabasePayload(UnifiedSheet, RawImportData = RawJSON)
        if (PortraitFileID is not None):
            Payload["SummaryData"]["PortraitFileID"] = PortraitFileID
            Payload["DetailData"]["PortraitFileID"] = PortraitFileID
            if (("PhysicalAppearance" in Payload["DetailData"]) and isinstance(Payload["DetailData"]["PhysicalAppearance"], dict)):
                Payload["DetailData"]["PhysicalAppearance"]["PortraitFileID"] = PortraitFileID

        CurrentTimestamp: DateTime.datetime = DateTime.datetime.now(DateTime.timezone.utc)
        NewCharacter: Character.Character = Character.Character(OwnerID = OwnerID, Name = Payload["Name"], GameSystem = Character.GameSystemType.DND5E, IsPublic = True, IsAccepted = False, IsProtected = Payload["IsProtected"], IsOverridden = Payload["IsOverridden"], ImportSource = Payload["ImportSource"], SummaryData = Payload["SummaryData"], DetailData = Payload["DetailData"], RawImportData = Payload["RawImportData"], CreatedAt = CurrentTimestamp, UpdatedAt = CurrentTimestamp)
        DatabaseSession.add(NewCharacter)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(NewCharacter)
        if not NewCharacter.IsAccepted:
            await Mailbox.DispatchAutomatedMail(DatabaseSession = DatabaseSession, RecipientUserID = NewCharacter.OwnerID, Subject = f"Character '{NewCharacter.Name}' Submitted for Review", Body = f"Greetings.\n\nYour imported character '{NewCharacter.Name}' ({NewCharacter.GameSystem.value}) has been placed into the queue for review by a character checker.\n\nYou will receive a notification once the review is completed.", Category = Mail.MailCategory.CharacterReview, RelatedEntityType = "Character", RelatedEntityID = NewCharacter.ID)

        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Imported Character Saved: \"{NewCharacter.Name}\" (ID=\"{NewCharacter.ID[:8]}…\")")
        return NewCharacter

    async def GetCharacterOverview(self, TargetURL: str) -> Typing.Dict[str, Typing.Any]:
        SourceType, CharacterID, UtilityName = self.DetectImportSource(TargetURL)
        if ((SourceType is None) or (CharacterID is None)):
            raise ValueError("Unrecognized character sheet URL. Please provide a valid Dicecloud or D&D Beyond URL.")

        RawJSON: Typing.Dict[str, Typing.Any] = await self.FetchCharacterData(SourceType, CharacterID)
        if (SourceType == "DC1"):
            UnifiedSheet: CharacterSchema.DND5ECharacterSheet = CharacterMapping.GLOBAL_CHARACTER_MAPPER.MapDC1Character(RawJSON)

        elif (SourceType == "DC2"):
            UnifiedSheet = CharacterMapping.GLOBAL_CHARACTER_MAPPER.MapDC2Character(RawJSON)

        elif (SourceType == "DDB"):
            UnifiedSheet = CharacterMapping.GLOBAL_CHARACTER_MAPPER.MapDDBCharacter(RawJSON)

        else:
            UnifiedSheet = CharacterMapping.GLOBAL_CHARACTER_MAPPER.IngestUniversalCharacterData(RawJSON)

        PrimaryClass: str = UnifiedSheet.Classes[0].ClassName if UnifiedSheet.Classes else "Adventurer"
        PortraitURL: Typing.Optional[str] = getattr(getattr(UnifiedSheet, "PhysicalAppearance", None), "PortraitURL", None)
        if not PortraitURL:
            if (SourceType == "DC1"):
                CharactersList: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("characters", [])
                CharacterData: Typing.Dict[str, Typing.Any] = CharactersList[0] if (CharactersList and isinstance(CharactersList[0], dict)) else {}
                PortraitURL = CharacterData.get("picture") or CharacterData.get("avatar") or RawJSON.get("picture") or RawJSON.get("avatar") or None

            elif (SourceType == "DC2"):
                CreaturesList: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("creatures", [])
                CreatureData: Typing.Dict[str, Typing.Any] = CreaturesList[0] if (CreaturesList and isinstance(CreaturesList[0], dict)) else {}
                PortraitURL = CreatureData.get("picture") or CreatureData.get("avatar") or None

            elif (SourceType == "DDB"):
                DataDictionary: Typing.Dict[str, Typing.Any] = RawJSON.get("data") if isinstance(RawJSON.get("data"), dict) else RawJSON
                PortraitURL = DataDictionary.get("avatarUrl") or (DataDictionary.get("decorations") or {}).get("avatarUrl") or None

        OverviewData: Typing.Dict[str, Typing.Any] = {
            "Name"       : UnifiedSheet.Name,
            "GameSystem" : "DND5E",
            "Source"     : UtilityName,
            "Class"      : PrimaryClass,
            "Level"      : UnifiedSheet.TotalLevel,
            "Species"    : UnifiedSheet.Species.FullName,
            "HitPoints"  : UnifiedSheet.HitPoints.MaxHitPoints,
            "ArmorClass" : UnifiedSheet.ArmorClass.TotalArmorClass,
            "PortraitURL": PortraitURL
        }
        return OverviewData

GLOBAL_CHARACTER_IMPORTER: CharacterImportService = CharacterImportService()
