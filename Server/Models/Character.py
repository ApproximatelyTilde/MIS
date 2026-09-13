import datetime        as DateTime
import enum            as Enumeration
import sqlalchemy      as SQLAlchemy
import sqlalchemy.orm  as ORM
import typing          as Typing
import uuid            as UUID

class GameSystemType(str, Enumeration.Enum):
    DND5thEdition       = "DND5thEdition"
    Traveller2ndEdition = "Traveller2ndEdition"

import Server.Database as Database

class Character(Database.Base):
    __tablename__ = "Characters"
    ID                  : ORM.Mapped[str]                                           = ORM.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UUID.uuid4()))
    OwnerID             : ORM.Mapped[str]                                           = ORM.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Users.ID", ondelete = "CASCADE"), nullable = False, index = True)
    Name                : ORM.Mapped[str]                                           = ORM.mapped_column(SQLAlchemy.String(150), nullable = False, index = True)
    GameSystem          : ORM.Mapped[GameSystemType]                                = ORM.mapped_column(SQLAlchemy.Enum(GameSystemType, name = "GameSystemType"), nullable = False, index = True)
    IsPublic            : ORM.Mapped[bool]                                          = ORM.mapped_column(SQLAlchemy.Boolean, default = True, nullable = False, index = True)
    IsArchived          : ORM.Mapped[bool]                                          = ORM.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False, index = True)
    IsPinned            : ORM.Mapped[bool]                                          = ORM.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False, index = True)
    IsAccepted          : ORM.Mapped[bool]                                          = ORM.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False, index = True)
    IsProtected         : ORM.Mapped[bool]                                          = ORM.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False, index = True)
    IsOverridden        : ORM.Mapped[bool]                                          = ORM.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False, index = True)
    ImportSource        : ORM.Mapped[str | None]                                    = ORM.mapped_column(SQLAlchemy.String(100), nullable = True)
    SummaryData         : ORM.Mapped[dict[str, Typing.Any]]                         = ORM.mapped_column(SQLAlchemy.JSON, default = dict, nullable = False)
    DetailData          : ORM.Mapped[dict[str, Typing.Any]]                         = ORM.mapped_column(SQLAlchemy.JSON, default = dict, nullable = False)
    RawImportData       : ORM.Mapped[dict[str, Typing.Any] | None]                  = ORM.mapped_column(SQLAlchemy.JSON, nullable = True)
    CreatedAt           : ORM.Mapped[DateTime.datetime]                             = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    UpdatedAt           : ORM.Mapped[DateTime.datetime]                             = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), onupdate = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    Owner               = ORM.relationship("User", back_populates = "Characters")
    StoryMemberships    = ORM.relationship("StoryMember", back_populates = "Character")
    EconomyTransactions = ORM.relationship("EconomyTransaction", back_populates = "Character", cascade = "all, delete-orphan")
