import datetime                                   as DateTime
import json                                       as JSONParser
import re                                         as RegularExpressions
import typing                                     as Typing
import httpx2                                     as HTTPClient
import sqlalchemy                                 as SQLAlchemy
import sqlalchemy.ext.asyncio                     as AsyncIO
import Server.Config                              as Config
import Server.Models.Character                    as Character
import Server.Models.DND5thEditionCharacterSchema as CharacterSchema
import Server.Models.Mail                         as Mail
import Server.Models.StorageFile                  as StorageFile
import Server.Models.User                         as User
import Server.Services.CharacterMappingService    as CharacterMappingService
import Server.Services.DebugService               as DebugService
import Server.Services.ImageProcessingService     as ImageProcessingService
import Server.Services.MailService                as MailService
import Server.Services.OracleStorageService       as OracleStorage

DICECLOUD_URL_PATTERN : RegularExpressions.Pattern = RegularExpressions.compile(r"(?:https?:\/\/)?v1\.dicecloud\.com\/character\/([a-zA-Z0-9_-]+)", RegularExpressions.IGNORECASE)
DNDBEYOND_URL_PATTERN : RegularExpressions.Pattern = RegularExpressions.compile(r"(?:https?:\/\/)?(?:www\.)?dndbeyond\.com\/characters\/(\d+)", RegularExpressions.IGNORECASE)
DNDBEYOND_PDF_PATTERN : RegularExpressions.Pattern = RegularExpressions.compile(r"(?:https?:\/\/)?(?:www\.)?dndbeyond\.com\/sheet-pdfs\/.*?[_-]?(\d+)\.pdf", RegularExpressions.IGNORECASE)
DNDBEYOND_SVC_PATTERN : RegularExpressions.Pattern = RegularExpressions.compile(r"(?:https?:\/\/)?character-service\.dndbeyond\.com\/character\/v5\/character\/(\d+)", RegularExpressions.IGNORECASE)

class CharacterImportService:
    def DetectImportSource(self, TargetURL: str) -> Typing.Tuple[Typing.Optional[str], Typing.Optional[str], Typing.Optional[str]]:
        CleanedURL: str = TargetURL.strip()
        DicecloudMatch  = DICECLOUD_URL_PATTERN.search(CleanedURL)
        if (DicecloudMatch is not None):
            CharacterID: str = DicecloudMatch.group(1)
            if (CharacterID.lower() != "json"):
                DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Detected Import Source: DicecloudV1 (ID=\"{CharacterID}\")")
                return ("DicecloudV1", CharacterID, "Dicecloud v1")

        DNDBeyondCharMatch = DNDBEYOND_URL_PATTERN.search(CleanedURL)
        if (DNDBeyondCharMatch is not None):
            CharacterID: str = DNDBeyondCharMatch.group(1)
            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Detected Import Source: DNDBeyond (ID=\"{CharacterID}\")")
            return ("DNDBeyond", CharacterID, "D&D Beyond")

        DNDBeyondPDFMatch = DNDBEYOND_PDF_PATTERN.search(CleanedURL)
        if (DNDBeyondPDFMatch is not None):
            CharacterID: str = DNDBeyondPDFMatch.group(1)
            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Detected Import Source: DNDBeyond PDF (ID=\"{CharacterID}\")")
            return ("DNDBeyond", CharacterID, "D&D Beyond")

        DNDBeyondSvcMatch = DNDBEYOND_SVC_PATTERN.search(CleanedURL)
        if (DNDBeyondSvcMatch is not None):
            CharacterID: str = DNDBeyondSvcMatch.group(1)
            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Detected Import Source: DNDBeyond Service (ID=\"{CharacterID}\")")
            return ("DNDBeyond", CharacterID, "D&D Beyond")

        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Failed to Detect Import Source for URL: \"{CleanedURL[:20]}…\"")
        return (None, None, None)

    async def DownloadAndStorePortrait(self, CurrentUser: User.User, PortraitURL: str, DatabaseSession: AsyncIO.AsyncSession) -> Typing.Optional[str]:
        if ((not PortraitURL) or (CurrentUser is None)):
            return None

        CleanedURL: str = PortraitURL.strip()
        if (len(CleanedURL) == 0):
            return None

        try:
            Headers: Typing.Dict[str, str] = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MIS/1.0",
                "Accept"    : "image/jpeg,image/png,image/webp,image/*"
            }
            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Downloading Character Portrait for User: \"{CurrentUser.ID[:8]}…\"")
            async with HTTPClient.AsyncClient(timeout = 20.0, follow_redirects = True) as ClientConnection:
                Response = await ClientConnection.get(CleanedURL, headers = Headers)
                if (Response.status_code != 200):
                    DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Portrait Download Failed: Status={Response.status_code}")
                    return None

                RawBytes: bytes = Response.content

            if (len(RawBytes) == 0):
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Portrait Download Returned Empty Response")
                return None

            SanitizedBytes, ContentType = ImageProcessingService.GLOBAL_IMAGE_PROCESSING_SERVICE.SanitizeAndOptimizeImage(RawBytes, "portrait.jpg")
            FileSizeBytes: int = len(SanitizedBytes)
            if not OracleStorage.GLOBAL_STORAGE_SERVICE.CheckQuotaAvailable(CurrentUser, FileSizeBytes):
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Portrait Storage Quota Exceeded for User: \"{CurrentUser.ID[:8]}…\"")
                return None

            OriginalFileName: str = "portrait.jpg"
            ObjectKey: Typing.Optional[str] = await OracleStorage.GLOBAL_STORAGE_SERVICE.UploadFile(CurrentUser, OriginalFileName, ContentType, SanitizedBytes)
            if not ObjectKey:
                DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = "Portrait Upload to Storage Provider Failed")
                return None

            NewStorageFile: StorageFile.StorageFile = StorageFile.StorageFile(OwnerID = CurrentUser.ID, FileName = OriginalFileName, ContentType = ContentType, FileSizeBytes = FileSizeBytes, ObjectKey = ObjectKey)
            DatabaseSession.add(NewStorageFile)
            CurrentUser.StorageUsedBytes += FileSizeBytes
            await DatabaseSession.commit()
            await DatabaseSession.refresh(NewStorageFile)
            DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Character Portrait Stored: FileID=\"{NewStorageFile.ID[:8]}…\", Size={FileSizeBytes}B")
            return NewStorageFile.ID

        except Exception as StorageError:
            DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Portrait Storage Error: {type(StorageError).__name__}")
            return None

    async def FetchCharacterData(self, SourceType: str, CharacterID: str) -> Typing.Dict[str, Typing.Any]:
        if (SourceType == "DicecloudV1"):
            APIKey: Typing.Optional[str] = Config.GLOBAL_SETTINGS.DICECLOUD_API_KEY
            if ((APIKey is None) or (len(APIKey.strip()) == 0)):
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Dicecloud Import Aborted: API Key Unconfigured")
                raise ValueError("Dicecloud API key is not configured in .env. Please set DICECLOUD_API_KEY to import from Dicecloud.")

            RequestURL: str = f"https://v1.dicecloud.com/character/{CharacterID}/json?key={APIKey.strip()}"
            Headers: Typing.Dict[str, str] = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MIS/1.0",
                "Accept"    : "application/json"
            }
            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Fetching Dicecloud Character: ID=\"{CharacterID}\"")
            try:
                async with HTTPClient.AsyncClient(timeout = 30.0) as ClientConnection:
                    Response = await ClientConnection.get(RequestURL, headers = Headers)

            except (HTTPClient.RequestError, HTTPClient.TimeoutException) as NetworkError:
                DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Dicecloud Connection Error: {type(NetworkError).__name__}")
                raise ValueError(f"Failed to connect to Dicecloud service: {type(NetworkError).__name__}")

            if ((Response.status_code == 401) or (Response.status_code == 403)):
                DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Dicecloud Authentication Failed: Status={Response.status_code}")
                raise ValueError("Dicecloud API key was rejected or unauthorized. Please verify your DICECLOUD_API_KEY in .env.")

            if (Response.status_code == 404):
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Dicecloud Character Not Found: ID=\"{CharacterID}\"")
                raise ValueError(f"Character '{CharacterID}' not found on Dicecloud. Verify the URL and ensure the sheet is accessible.")

            if (Response.status_code != 200):
                DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Dicecloud Request Failed: Status={Response.status_code}")
                raise ValueError(f"Failed to fetch character from Dicecloud (HTTP {Response.status_code}).")

            try:
                ParsedData: Typing.Dict[str, Typing.Any] = Response.json()

            except Exception as ParsingError:
                DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Dicecloud JSON Parse Error: {type(ParsingError).__name__}")
                raise ValueError("Received invalid or corrupted JSON data from Dicecloud.")

            if (isinstance(ParsedData, dict) and ("error" in ParsedData)):
                ErrorMessage: str = str(ParsedData["error"])
                DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Dicecloud API Error: \"{ErrorMessage[:35]}\"")
                raise ValueError(f"Dicecloud API error: {ErrorMessage}")

            return ParsedData

        if (SourceType == "DNDBeyond"):
            RequestURL: str = f"https://character-service.dndbeyond.com/character/v5/character/{CharacterID}"
            Headers: Typing.Dict[str, str] = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept"    : "application/json"
            }
            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Fetching DNDBeyond Character: ID=\"{CharacterID}\"")
            try:
                async with HTTPClient.AsyncClient(timeout = 30.0, follow_redirects = True) as ClientConnection:
                    Response = await ClientConnection.get(RequestURL, headers = Headers)

            except (HTTPClient.RequestError, HTTPClient.TimeoutException) as NetworkError:
                DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"DNDBeyond Connection Error: {type(NetworkError).__name__}")
                raise ValueError(f"Failed to connect to D&D Beyond service: {type(NetworkError).__name__}")

            if (Response.status_code == 403):
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"DNDBeyond Access Forbidden: ID=\"{CharacterID}\"")
                raise ValueError(f"Access forbidden by D&D Beyond for character '{CharacterID}'. Please make sure the character sheet is set to Public.")

            if (Response.status_code == 404):
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"DNDBeyond Character Not Found: ID=\"{CharacterID}\"")
                raise ValueError(f"Character '{CharacterID}' was not found on D&D Beyond.")

            if (Response.status_code != 200):
                DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"DNDBeyond Request Failed: Status={Response.status_code}")
                raise ValueError(f"Failed to fetch character from D&D Beyond (HTTP {Response.status_code}).")

            try:
                ParsedData: Typing.Dict[str, Typing.Any] = Response.json()

            except Exception as ParsingError:
                DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"DNDBeyond JSON Parse Error: {type(ParsingError).__name__}")
                raise ValueError("Received invalid or corrupted JSON data from D&D Beyond.")

            if (isinstance(ParsedData, dict) and (ParsedData.get("success") is False)):
                ErrorMessage: str = str(ParsedData.get("message") or "Unknown error from D&D Beyond")
                DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"DNDBeyond API Error: \"{ErrorMessage[:35]}\"")
                raise ValueError(f"D&D Beyond error: {ErrorMessage}")

            return ParsedData

        raise ValueError(f"Unsupported import source: '{SourceType}'")

    async def ImportCharacterFromURL(self, TargetURL: str, OwnerID: str, DatabaseSession: AsyncIO.AsyncSession) -> Character.Character:
        SourceType, CharacterID, UtilityName = self.DetectImportSource(TargetURL)
        if ((SourceType is None) or (CharacterID is None)):
            raise ValueError("Unrecognized character sheet URL. Please provide a valid Dicecloud v1 or D&D Beyond URL.")

        RawJSON: Typing.Dict[str, Typing.Any] = await self.FetchCharacterData(SourceType, CharacterID)
        if (SourceType == "DicecloudV1"):
            UnifiedSheet: CharacterSchema.DND5thEditionCharacterSheet = CharacterMappingService.GLOBAL_CHARACTER_MAPPER.MapDicecloudCharacter(RawJSON)

        elif (SourceType == "DNDBeyond"):
            UnifiedSheet: CharacterSchema.DND5thEditionCharacterSheet = CharacterMappingService.GLOBAL_CHARACTER_MAPPER.MapDNDBeyondCharacter(RawJSON)

        else:
            UnifiedSheet: CharacterSchema.DND5thEditionCharacterSheet = CharacterMappingService.GLOBAL_CHARACTER_MAPPER.IngestUniversalCharacterData(RawJSON)

        UserQueryStatement = SQLAlchemy.select(User.User).where(User.User.ID == OwnerID)
        UserQueryResult    = await DatabaseSession.execute(UserQueryStatement)
        CurrentUser: Typing.Optional[User.User] = UserQueryResult.scalars().first()

        PortraitURL: Typing.Optional[str] = getattr(getattr(UnifiedSheet, "PhysicalAppearance", None), "PortraitURL", None)
        PortraitFileID: Typing.Optional[str] = None
        if ((PortraitURL is not None) and (CurrentUser is not None)):
            PortraitFileID = await self.DownloadAndStorePortrait(CurrentUser, PortraitURL, DatabaseSession)

        if ((PortraitFileID is not None) and (UnifiedSheet.PhysicalAppearance is not None)):
            UnifiedSheet.PhysicalAppearance.PortraitFileID = PortraitFileID

        Payload: Typing.Dict[str, Typing.Any] = CharacterMappingService.GLOBAL_CHARACTER_MAPPER.ExportToDatabasePayload(UnifiedSheet, RawImportData = RawJSON)
        if (PortraitFileID is not None):
            Payload["SummaryData"]["PortraitFileID"] = PortraitFileID
            Payload["DetailData"]["PortraitFileID"] = PortraitFileID
            if ("PhysicalAppearance" in Payload["DetailData"]) and isinstance(Payload["DetailData"]["PhysicalAppearance"], dict):
                Payload["DetailData"]["PhysicalAppearance"]["PortraitFileID"] = PortraitFileID

        CurrentTimestamp: DateTime.datetime = DateTime.datetime.now(DateTime.timezone.utc)
        NewCharacter: Character.Character = Character.Character(OwnerID = OwnerID, Name = Payload["Name"], GameSystem = Character.GameSystemType.DND5thEdition, IsPublic = True, IsAccepted = False, IsProtected = Payload["IsProtected"], IsOverridden = Payload["IsOverridden"], ImportSource = Payload["ImportSource"], SummaryData = Payload["SummaryData"], DetailData = Payload["DetailData"], RawImportData = Payload["RawImportData"], CreatedAt = CurrentTimestamp, UpdatedAt = CurrentTimestamp)
        DatabaseSession.add(NewCharacter)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(NewCharacter)
        if not NewCharacter.IsAccepted:
            await MailService.DispatchAutomatedMail(DatabaseSession = DatabaseSession, RecipientUserID = NewCharacter.OwnerID, Subject = f"Character '{NewCharacter.Name}' Submitted for Review", Body = f"Greetings.\n\nYour imported character '{NewCharacter.Name}' ({NewCharacter.GameSystem.value}) has been placed into the queue for review by a character checker.\n\nYou will receive a notification once the review is completed.", Category = Mail.MailCategory.CharacterReview, RelatedEntityType = "Character", RelatedEntityID = NewCharacter.ID)

        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Imported Character Saved: \"{NewCharacter.Name}\" (ID=\"{NewCharacter.ID[:8]}…\")")
        return NewCharacter

    async def GetCharacterOverview(self, TargetURL: str) -> Typing.Dict[str, Typing.Any]:
        SourceType, CharacterID, UtilityName = self.DetectImportSource(TargetURL)
        if ((SourceType is None) or (CharacterID is None)):
            raise ValueError("Unrecognized character sheet URL. Please provide a valid Dicecloud v1 or D&D Beyond URL.")

        RawJSON: Typing.Dict[str, Typing.Any] = await self.FetchCharacterData(SourceType, CharacterID)
        if (SourceType == "DicecloudV1"):
            UnifiedSheet: CharacterSchema.DND5thEditionCharacterSheet = CharacterMappingService.GLOBAL_CHARACTER_MAPPER.MapDicecloudCharacter(RawJSON)

        elif (SourceType == "DNDBeyond"):
            UnifiedSheet: CharacterSchema.DND5thEditionCharacterSheet = CharacterMappingService.GLOBAL_CHARACTER_MAPPER.MapDNDBeyondCharacter(RawJSON)

        else:
            UnifiedSheet: CharacterSchema.DND5thEditionCharacterSheet = CharacterMappingService.GLOBAL_CHARACTER_MAPPER.IngestUniversalCharacterData(RawJSON)

        PrimaryClass: str = UnifiedSheet.Classes[0].ClassName if UnifiedSheet.Classes else "Adventurer"
        PortraitURL: Typing.Optional[str] = getattr(getattr(UnifiedSheet, "PhysicalAppearance", None), "PortraitURL", None)
        if not PortraitURL:
            if (SourceType == "DicecloudV1"):
                CharactersList: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("characters", [])
                CharacterData: Typing.Dict[str, Typing.Any] = CharactersList[0] if (CharactersList and isinstance(CharactersList[0], dict)) else {}
                PortraitURL = CharacterData.get("picture") or CharacterData.get("avatar") or RawJSON.get("picture") or RawJSON.get("avatar") or None

            elif (SourceType == "DNDBeyond"):
                DataDictionary: Typing.Dict[str, Typing.Any] = RawJSON.get("data") if isinstance(RawJSON.get("data"), dict) else RawJSON
                PortraitURL = DataDictionary.get("avatarUrl") or (DataDictionary.get("decorations") or {}).get("avatarUrl") or None

        OverviewData: Typing.Dict[str, Typing.Any] = {
            "Name"       : UnifiedSheet.Name,
            "GameSystem" : "DND5thEdition",
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
