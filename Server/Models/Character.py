import datetime        as DateTime
import enum            as Enumeration
import sqlalchemy      as SQLAlchemy
import sqlalchemy.orm  as ObjectRelationalMapper
import typing          as Typing
import uuid            as UniversallyUniqueIdentifier
import Server.Database as Database

class GameSystemType(str, Enumeration.Enum):
    DND5thEdition = "DND5thEdition"
    Traveller2ndEdition = "Traveller2ndEdition"

class Character(Database.Base):
    __tablename__ = "Characters"
    Identifier     : ObjectRelationalMapper.Mapped[str]                                           = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UniversallyUniqueIdentifier.uuid4()))
    OwnerIdentifier: ObjectRelationalMapper.Mapped[str]                                           = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Users.Identifier", ondelete = "CASCADE"), nullable = False, index = True)
    Name           : ObjectRelationalMapper.Mapped[str]                                           = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(150), nullable = False, index = True)
    GameSystem     : ObjectRelationalMapper.Mapped[GameSystemType]                                = ObjectRelationalMapper.mapped_column(SQLAlchemy.Enum(GameSystemType, name = "GameSystemType"), nullable = False, index = True)
    IsPublic       : ObjectRelationalMapper.Mapped[bool]                                          = ObjectRelationalMapper.mapped_column(SQLAlchemy.Boolean, default = True, nullable = False, index = True)
    IsArchived     : ObjectRelationalMapper.Mapped[bool]                                          = ObjectRelationalMapper.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False, index = True)
    IsPinned       : ObjectRelationalMapper.Mapped[bool]                                          = ObjectRelationalMapper.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False, index = True)
    IsAccepted     : ObjectRelationalMapper.Mapped[bool]                                          = ObjectRelationalMapper.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False, index = True)
    SummaryData    : ObjectRelationalMapper.Mapped[Typing.Dict[str, Typing.Any]]                  = ObjectRelationalMapper.mapped_column(SQLAlchemy.JSON, default = dict, nullable = False)
    DetailData     : ObjectRelationalMapper.Mapped[Typing.Dict[str, Typing.Any]]                  = ObjectRelationalMapper.mapped_column(SQLAlchemy.JSON, default = dict, nullable = False)
    RawImportData  : ObjectRelationalMapper.Mapped[Typing.Optional[Typing.Dict[str, Typing.Any]]] = ObjectRelationalMapper.mapped_column(SQLAlchemy.JSON, nullable = True)
    CreatedAt      : ObjectRelationalMapper.Mapped[DateTime.datetime]                             = ObjectRelationalMapper.mapped_column(SQLAlchemy.DateTime(timezone = True), default = DateTime.datetime.utcnow, nullable = False)
    UpdatedAt      : ObjectRelationalMapper.Mapped[DateTime.datetime]                             = ObjectRelationalMapper.mapped_column(SQLAlchemy.DateTime(timezone = True), default = DateTime.datetime.utcnow, onupdate = DateTime.datetime.utcnow, nullable = False)
    Owner               = ObjectRelationalMapper.relationship("User", back_populates = "Characters")
    StoryMemberships    = ObjectRelationalMapper.relationship("StoryMember", back_populates = "Character")
    EconomyTransactions = ObjectRelationalMapper.relationship("EconomyTransaction", back_populates = "Character", cascade = "all, delete-orphan")
