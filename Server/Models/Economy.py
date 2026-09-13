import datetime                as DateTime
import sqlalchemy              as SQLAlchemy
import sqlalchemy.orm          as ORM
import typing                  as Typing
import uuid                    as UUID
import Server.Database         as Database
import Server.Models.Character as Character

class EconomyTransaction(Database.Base):
    __tablename__ = "EconomyTransactions"
    ID               : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UUID.uuid4()))
    CharacterID      : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Characters.ID", ondelete = "CASCADE"), nullable = False, index = True)
    InitiatorID      : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Users.ID", ondelete = "CASCADE"), nullable = False, index = True)
    GameSystem       : ORM.Mapped[Character.GameSystemType] = ORM.mapped_column(SQLAlchemy.Enum(Character.GameSystemType), nullable = False, index = True)
    AmountChange     : ORM.Mapped[float]                    = ORM.mapped_column(SQLAlchemy.Float, default = 0.0, nullable = False)
    CurrencyType     : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(50), default = "Gold", nullable = False)
    ItemName         : ORM.Mapped[Typing.Optional[str]]     = ORM.mapped_column(SQLAlchemy.String(150), nullable = True)
    QuantityChange   : ORM.Mapped[int]                      = ORM.mapped_column(SQLAlchemy.Integer, default = 0, nullable = False)
    TransactionReason: ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(255), default = "General Transaction", nullable = False)
    CreatedAt        : ORM.Mapped[DateTime.datetime]        = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    Character        = ORM.relationship("Character", back_populates = "EconomyTransactions")
    Initiator        = ORM.relationship("User")
