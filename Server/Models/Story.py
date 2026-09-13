import datetime                as DateTime
import enum                    as Enumeration
import sqlalchemy              as SQLAlchemy
import sqlalchemy.orm          as ObjectRelationalMapper
import typing                  as Typing
import uuid                    as UniversallyUniqueIdentifier
import Server.Database         as Database
import Server.Models.Character as Character

class StoryMembershipStatus(str, Enumeration.Enum):
    Requested = "Requested"
    Invited   = "Invited"
    Active    = "Active"
    Rejected  = "Rejected"

class Story(Database.Base):
    __tablename__ = "Stories"
    Identifier          : ObjectRelationalMapper.Mapped[str]                      = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UniversallyUniqueIdentifier.uuid4()))
    GameMasterIdentifier: ObjectRelationalMapper.Mapped[str]                      = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Users.Identifier", ondelete = "CASCADE"), nullable = False, index = True)
    Title               : ObjectRelationalMapper.Mapped[str]                      = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(200), nullable = False, index = True)
    Description         : ObjectRelationalMapper.Mapped[str]                      = ObjectRelationalMapper.mapped_column(SQLAlchemy.Text, default = "", nullable = False)
    GameSystem          : ObjectRelationalMapper.Mapped[Character.GameSystemType] = ObjectRelationalMapper.mapped_column(SQLAlchemy.Enum(Character.GameSystemType, name = "GameSystemType"), nullable = False, index = True)
    IsPublic            : ObjectRelationalMapper.Mapped[bool]                     = ObjectRelationalMapper.mapped_column(SQLAlchemy.Boolean, default = True, nullable = False, index = True)
    IsArchived          : ObjectRelationalMapper.Mapped[bool]                     = ObjectRelationalMapper.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False, index = True)
    CreatedAt           : ObjectRelationalMapper.Mapped[DateTime.datetime]        = ObjectRelationalMapper.mapped_column(SQLAlchemy.DateTime(timezone = True), default = DateTime.datetime.utcnow, nullable = False)
    UpdatedAt           : ObjectRelationalMapper.Mapped[DateTime.datetime]        = ObjectRelationalMapper.mapped_column(SQLAlchemy.DateTime(timezone = True), default = DateTime.datetime.utcnow, onupdate = DateTime.datetime.utcnow, nullable = False)
    GameMaster = ObjectRelationalMapper.relationship("User", back_populates = "ManagedStories")
    Members    = ObjectRelationalMapper.relationship("StoryMember", back_populates = "Story", cascade = "all, delete-orphan")

class StoryMember(Database.Base):
    __tablename__ = "StoryMembers"
    Identifier         : ObjectRelationalMapper.Mapped[str]                   = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UniversallyUniqueIdentifier.uuid4()))
    StoryIdentifier    : ObjectRelationalMapper.Mapped[str]                   = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Stories.Identifier", ondelete = "CASCADE"), nullable = False, index = True)
    UserIdentifier     : ObjectRelationalMapper.Mapped[str]                   = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Users.Identifier", ondelete = "CASCADE"), nullable = False, index = True)
    CharacterIdentifier: ObjectRelationalMapper.Mapped[Typing.Optional[str]]  = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Characters.Identifier", ondelete = "SET NULL"), nullable = True, index = True)
    MembershipStatus   : ObjectRelationalMapper.Mapped[StoryMembershipStatus] = ObjectRelationalMapper.mapped_column(SQLAlchemy.Enum(StoryMembershipStatus, name = "StoryMembershipStatus"), default = StoryMembershipStatus.Requested, nullable = False)
    CreatedAt          : ObjectRelationalMapper.Mapped[DateTime.datetime]     = ObjectRelationalMapper.mapped_column(SQLAlchemy.DateTime(timezone = True), default = DateTime.datetime.utcnow, nullable = False)
    UpdatedAt          : ObjectRelationalMapper.Mapped[DateTime.datetime]     = ObjectRelationalMapper.mapped_column(SQLAlchemy.DateTime(timezone = True), default = DateTime.datetime.utcnow, onupdate = DateTime.datetime.utcnow, nullable = False)
    Story     = ObjectRelationalMapper.relationship("Story", back_populates = "Members")
    User      = ObjectRelationalMapper.relationship("User", back_populates = "StoryMemberships")
    Character = ObjectRelationalMapper.relationship("Character", back_populates = "StoryMemberships")
