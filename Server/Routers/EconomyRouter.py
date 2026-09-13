import typing                                  as Typing
import fastapi                                 as FastAPI
import fastapi.responses                       as Responses
import pydantic                                as Pydantic
import sqlalchemy                              as SQLAlchemy
import sqlalchemy.ext.asyncio                  as AsyncIO
import Server.Auth.RoleBasedAccessControl      as RoleBasedAccessControl
import Server.Database                         as Database
import Server.Models.Character                 as Character
import Server.Models.Economy                   as Economy
import Server.Models.User                      as User
import Server.Services.DebugService            as DebugService
import Server.Services.TemplateRendererService as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Economy", tags = ["Economy"])

@Router.get("/Ledger/Partial", response_class = Responses.HTMLResponse)
async def GetCharacterLedgerPartial(CharacterID: str | None = None, CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    if not CharacterID:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Ledger Partial Skipped: Missing Character ID")
        return TemplateRenderer.RenderPartialResponse("Economy/LedgerTableRowsPartial.html", {"InfoMessage": "Select a character above to load transaction ledger."})

    CharacterQuery = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    CharacterResult = await DatabaseSession.execute(CharacterQuery)
    TargetCharacter: Character.Character | None = CharacterResult.scalars().first()
    if not TargetCharacter:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Character Not Found for Ledger: ID=\"{CharacterID[:8]}…\"")
        return TemplateRenderer.RenderPartialResponse("Economy/LedgerTableRowsPartial.html", {"ErrorMessage": "Character not found."})

    if not RoleBasedAccessControl.CanViewCharacter(CurrentUser, TargetCharacter):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Ledger Access Forbidden for Character: ID=\"{CharacterID[:8]}…\"")
        return TemplateRenderer.RenderPartialResponse("Economy/LedgerTableRowsPartial.html", {"ErrorMessage": "Access forbidden under current permissions."})

    QueryStatement = SQLAlchemy.select(Economy.EconomyTransaction).where(Economy.EconomyTransaction.CharacterID == CharacterID).order_by(Economy.EconomyTransaction.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    Transactions = QueryResult.scalars().all()
    if not Transactions:
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Character Ledger Empty: ID=\"{CharacterID[:8]}…\"")
        return TemplateRenderer.RenderPartialResponse("Economy/LedgerTableRowsPartial.html", {"InfoMessage": "No transactions recorded for this character yet."})

    FormattedTransactions: list[dict[str, Typing.Any]] = []
    for Transaction in Transactions:
        AmountClass: str = "TextGreen" if (Transaction.AmountChange >= 0) else "TextDanger"
        ItemStr: str = f"{Transaction.QuantityChange:+d} {Transaction.ItemName}" if Transaction.ItemName else "-"
        AmountFormattedString: str = f"{Transaction.AmountChange:+.2f} {Transaction.CurrencyType}"
        TransactionEntry: dict[str, Typing.Any] = {
            "FormattedDate"  : Transaction.CreatedAt.strftime("%Y-%m-%d"),
            "GameSystem"     : Transaction.GameSystem.value,
            "Reason"         : Transaction.TransactionReason,
            "AmountClass"    : AmountClass,
            "AmountFormatted": AmountFormattedString,
            "ItemFormatted"  : ItemStr
        }
        FormattedTransactions.append(TransactionEntry)

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Rendered Character Ledger: Count={len(FormattedTransactions)}, ID=\"{CharacterID[:8]}…\"")
    return TemplateRenderer.RenderPartialResponse("Economy/LedgerTableRowsPartial.html", {"Transactions": FormattedTransactions})
