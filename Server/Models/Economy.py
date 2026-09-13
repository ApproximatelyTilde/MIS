import datetime                as DateTime
import sqlalchemy              as SQLAlchemy
import sqlalchemy.orm          as ObjectRelationalMapper
import typing                  as Typing
import uuid                    as UniversallyUniqueIdentifier
import Server.Database         as Database
import Server.Models.Character as Character

class EconomyTransaction(Database.Base):
    __tablename__ = "EconomyTransactions"
    Identifier         : ObjectRelationalMapper.Mapped[str]                      = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UniversallyUniqueIdentifier.uuid4()))
    CharacterIdentifier: ObjectRelationalMapper.Mapped[str]                      = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Characters.Identifier", ondelete = "CASCADE"), nullable = False, index = True)
    InitiatorIdentifier: ObjectRelationalMapper.Mapped[str]                      = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Users.Identifier", ondelete = "CASCADE"), nullable = False, index = True)
    GameSystem         : ObjectRelationalMapper.Mapped[Character.GameSystemType] = ObjectRelationalMapper.mapped_column(SQLAlchemy.Enum(Character.GameSystemType), nullable = False, index = True)
    AmountChange       : ObjectRelationalMapper.Mapped[float]                    = ObjectRelationalMapper.mapped_column(SQLAlchemy.Float, default = 0.0, nullable = False)
    CurrencyType       : ObjectRelationalMapper.Mapped[str]                      = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(50), default = "Gold", nullable = False)
    ItemName           : ObjectRelationalMapper.Mapped[Typing.Optional[str]]     = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(150), nullable = True)
    QuantityChange     : ObjectRelationalMapper.Mapped[int]                      = ObjectRelationalMapper.mapped_column(SQLAlchemy.Integer, default = 0, nullable = False)
    TransactionReason  : ObjectRelationalMapper.Mapped[str]                      = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(255), default = "General Transaction", nullable = False)
    CreatedAt          : ObjectRelationalMapper.Mapped[DateTime.datetime]        = ObjectRelationalMapper.mapped_column(SQLAlchemy.DateTime(timezone = True), default = DateTime.datetime.utcnow, nullable = False)
    Character = ObjectRelationalMapper.relationship("Character", back_populates = "EconomyTransactions")
    Initiator = ObjectRelationalMapper.relationship("User")
