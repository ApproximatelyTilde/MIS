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
import Server.Services.DebugService             as DebugService
import Server.Services.TemplateRendererService as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Economy", tags = ["Economy"])

@Router.get("/Ledger/Partial", response_class = Responses.HTMLResponse)
async def GetCharacterLedgerPartial(CharacterIdentifier: Typing.Optional[str] = None, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if not CharacterIdentifier:
        DebugService.LogDebugMessage(f"Ledger Partial Skipped: Missing CharacterIdentifier (User={getattr(CurrentUser, 'Identifier', None)})")
        return TemplateRenderer.RenderPartialResponse("Economy/LedgerTableRowsPartial.html", {"InfoMessage": "Select a character above to load transaction ledger."})

    CharQuery = SQLAlchemy.select(Character.Character).where(Character.Character.Identifier == CharacterIdentifier)
    CharResult = await DatabaseSession.execute(CharQuery)
    TargetCharacter: Typing.Optional[Character.Character] = CharResult.scalars().first()
    if not TargetCharacter:
        DebugService.LogDebugMessage(f"Ledger Partial Failed: Character '{CharacterIdentifier}' Not Found (User={getattr(CurrentUser, 'Identifier', None)})")
        return TemplateRenderer.RenderPartialResponse("Economy/LedgerTableRowsPartial.html", {"ErrorMessage": "Character not found."})

    if not RoleBasedAccessControl.CanViewCharacter(CurrentUser, TargetCharacter):
        DebugService.LogDebugMessage(f"Ledger Partial Forbidden: Character '{CharacterIdentifier}' (User={getattr(CurrentUser, 'Identifier', None)})")
        return TemplateRenderer.RenderPartialResponse("Economy/LedgerTableRowsPartial.html", {"ErrorMessage": "Access forbidden under current permissions."})

    QueryStatement = SQLAlchemy.select(Economy.EconomyTransaction).where(Economy.EconomyTransaction.CharacterIdentifier == CharacterIdentifier).order_by(Economy.EconomyTransaction.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    Transactions = QueryResult.scalars().all()
    if not Transactions:
        DebugService.LogDebugMessage(f"Ledger Partial Empty: Character '{CharacterIdentifier}' Has 0 Transactions (User={getattr(CurrentUser, 'Identifier', None)})")
        return TemplateRenderer.RenderPartialResponse("Economy/LedgerTableRowsPartial.html", {"InfoMessage": "No transactions recorded for this character yet."})

    FormattedTransactions: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for Transaction in Transactions:
        AmountClass: str = "TextGreen" if (Transaction.AmountChange >= 0) else "TextDanger"
        ItemStr: str = f"{Transaction.QuantityChange:+d} {Transaction.ItemName}" if Transaction.ItemName else "-"
        FormattedTransactions.append({
            "FormattedDate"  : Transaction.CreatedAt.strftime("%Y-%m-%d"),
            "GameSystem"     : Transaction.GameSystem.value,
            "Reason"         : Transaction.TransactionReason,
            "AmountClass"    : AmountClass,
            "AmountFormatted": f"{Transaction.AmountChange:+d} {Transaction.CurrencyType}",
            "ItemFormatted"  : ItemStr
        })

    DebugService.LogDebugMessage(f"Ledger Partial Rendered: Character '{CharacterIdentifier}' ({len(FormattedTransactions)} Transactions, User={getattr(CurrentUser, 'Identifier', None)})")
    return TemplateRenderer.RenderPartialResponse("Economy/LedgerTableRowsPartial.html", {"Transactions": FormattedTransactions})
