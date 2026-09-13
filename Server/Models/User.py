import datetime        as DateTime
import enum            as Enumeration
import typing          as Typing
import uuid            as UUID
import sqlalchemy      as SQLAlchemy
import sqlalchemy.orm  as ORM
import Server.Database as Database

class UserRole(str, Enumeration.Enum):
    Visitor       = "Visitor"
    NormalUser    = "NormalUser"
    Checker       = "Checker"
    GameMaster    = "GameMaster"
    Administrator = "Administrator"

class User(Database.Base):
    __tablename__ = "Users"
    ID              : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UUID.uuid4()))
    DiscordID       : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(64), unique = True, index = True, nullable = False)
    Username        : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(100), nullable = False)
    DisplayName     : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(100), nullable = False)
    AvatarHash      : ORM.Mapped[str | None]               = ORM.mapped_column(SQLAlchemy.String(128), nullable = True)
    Role            : ORM.Mapped[UserRole]                 = ORM.mapped_column(SQLAlchemy.Enum(UserRole, name = "UserRole"), default = UserRole.NormalUser, nullable = False)
    Roles           : ORM.Mapped[list[str]]                = ORM.mapped_column(SQLAlchemy.JSON, default = list, nullable = False)
    StorageUsedBytes: ORM.Mapped[int]                      = ORM.mapped_column(SQLAlchemy.BigInteger, default = 0, nullable = False)
    LastActiveAt    : ORM.Mapped[DateTime.datetime | None] = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), nullable = True)
    CreatedAt       : ORM.Mapped[DateTime.datetime]        = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    UpdatedAt       : ORM.Mapped[DateTime.datetime]        = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), onupdate = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    Characters       = ORM.relationship("Character", back_populates = "Owner", cascade = "all, delete-orphan")
    StorageFiles     = ORM.relationship("StorageFile", back_populates = "Owner", cascade = "all, delete-orphan")
    StoryMemberships = ORM.relationship("StoryMember", back_populates = "User", cascade = "all, delete-orphan")
    ManagedStories   = ORM.relationship("Story", back_populates = "GameMaster")
    SentMail         = ORM.relationship("MailMessage", foreign_keys = "MailMessage.SenderUserID", back_populates = "Sender")
    ReceivedMail     = ORM.relationship("MailMessage", foreign_keys = "MailMessage.RecipientUserID", back_populates = "Recipient", cascade = "all, delete-orphan")
