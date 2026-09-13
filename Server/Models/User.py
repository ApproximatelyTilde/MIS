import datetime        as DateTime
import enum            as Enumeration
import typing          as Typing
import uuid            as UniversallyUniqueIdentifier
import sqlalchemy      as SQLAlchemy
import sqlalchemy.orm  as ObjectRelationalMapper
import Server.Database as Database

class UserRole(str, Enumeration.Enum):
    Visitor       = "Visitor"
    NormalUser    = "NormalUser"
    Checker       = "Checker"
    GameMaster    = "GameMaster"
    Administrator = "Administrator"

class User(Database.Base):
    __tablename__ = "Users"
    Identifier       : ObjectRelationalMapper.Mapped[str]                  = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UniversallyUniqueIdentifier.uuid4()))
    DiscordIdentifier: ObjectRelationalMapper.Mapped[str]                  = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(64), unique = True, index = True, nullable = False)
    Username         : ObjectRelationalMapper.Mapped[str]                  = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(100), nullable = False)
    DisplayName      : ObjectRelationalMapper.Mapped[str]                  = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(100), nullable = False)
    AvatarHash       : ObjectRelationalMapper.Mapped[Typing.Optional[str]] = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(128), nullable = True)
    Role             : ObjectRelationalMapper.Mapped[UserRole]             = ObjectRelationalMapper.mapped_column(SQLAlchemy.Enum(UserRole, name = "UserRole"), default = UserRole.NormalUser, nullable = False)
    Roles            : ObjectRelationalMapper.Mapped[Typing.List[str]]     = ObjectRelationalMapper.mapped_column(SQLAlchemy.JSON, default = list, nullable = False)
    StorageUsedBytes : ObjectRelationalMapper.Mapped[int]                  = ObjectRelationalMapper.mapped_column(SQLAlchemy.BigInteger, default = 0, nullable = False)
    CreatedAt        : ObjectRelationalMapper.Mapped[DateTime.datetime]    = ObjectRelationalMapper.mapped_column(SQLAlchemy.DateTime(timezone = True), default = DateTime.datetime.utcnow, nullable = False)
    UpdatedAt        : ObjectRelationalMapper.Mapped[DateTime.datetime]    = ObjectRelationalMapper.mapped_column(SQLAlchemy.DateTime(timezone = True), default = DateTime.datetime.utcnow, onupdate = DateTime.datetime.utcnow, nullable = False)
    Characters       = ObjectRelationalMapper.relationship("Character", back_populates = "Owner", cascade = "all, delete-orphan")
    StorageFiles     = ObjectRelationalMapper.relationship("StorageFile", back_populates = "Owner", cascade = "all, delete-orphan")
    StoryMemberships = ObjectRelationalMapper.relationship("StoryMember", back_populates = "User", cascade = "all, delete-orphan")
    ManagedStories   = ObjectRelationalMapper.relationship("Story", back_populates = "GameMaster")
