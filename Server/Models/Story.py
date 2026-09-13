import datetime                as DateTime
import enum                    as Enumeration
import sqlalchemy              as SQLAlchemy
import sqlalchemy.orm          as ORM
import typing                  as Typing
import uuid                    as UUID
import Server.Database         as Database
import Server.Models.Character as Character

class StoryMembershipStatus(str, Enumeration.Enum):
    Requested = "Requested"
    Invited   = "Invited"
    Active    = "Active"
    Rejected  = "Rejected"

class Story(Database.Base):
    __tablename__ = "Stories"
    ID          : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UUID.uuid4()))
    GameMasterID: ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Users.ID", ondelete = "CASCADE"), nullable = False, index = True)
    Title       : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(200), nullable = False, index = True)
    Description : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.Text, default = "", nullable = False)
    GameSystem  : ORM.Mapped[Character.GameSystemType] = ORM.mapped_column(SQLAlchemy.Enum(Character.GameSystemType, name = "GameSystemType"), nullable = False, index = True)
    IsPublic    : ORM.Mapped[bool]                     = ORM.mapped_column(SQLAlchemy.Boolean, default = True, nullable = False, index = True)
    IsArchived  : ORM.Mapped[bool]                     = ORM.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False, index = True)
    CreatedAt   : ORM.Mapped[DateTime.datetime]        = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    UpdatedAt   : ORM.Mapped[DateTime.datetime]        = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), onupdate = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    GameMaster  = ORM.relationship("User", back_populates = "ManagedStories")
    Members     = ORM.relationship("StoryMember", back_populates = "Story", cascade = "all, delete-orphan")

class StoryMember(Database.Base):
    __tablename__ = "StoryMembers"
    ID              : ORM.Mapped[str]                   = ORM.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UUID.uuid4()))
    StoryID         : ORM.Mapped[str]                   = ORM.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Stories.ID", ondelete = "CASCADE"), nullable = False, index = True)
    UserID          : ORM.Mapped[str]                   = ORM.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Users.ID", ondelete = "CASCADE"), nullable = False, index = True)
    CharacterID     : ORM.Mapped[str | None]            = ORM.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Characters.ID", ondelete = "SET NULL"), nullable = True, index = True)
    MembershipStatus: ORM.Mapped[StoryMembershipStatus] = ORM.mapped_column(SQLAlchemy.Enum(StoryMembershipStatus, name = "StoryMembershipStatus"), default = StoryMembershipStatus.Requested, nullable = False)
    CreatedAt       : ORM.Mapped[DateTime.datetime]     = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    UpdatedAt       : ORM.Mapped[DateTime.datetime]     = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), onupdate = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    Story           = ORM.relationship("Story", back_populates = "Members")
    User            = ORM.relationship("User", back_populates = "StoryMemberships")
    Character       = ORM.relationship("Character", back_populates = "StoryMemberships")
