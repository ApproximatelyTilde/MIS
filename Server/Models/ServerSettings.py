import datetime        as DateTime
import uuid            as UUID
import sqlalchemy      as SQLAlchemy
import sqlalchemy.orm  as ORM
import Server.Database as Database

class ServerSettings(Database.Base):
    __tablename__ = "ServerSettings"
    ID                    : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UUID.uuid4()))
    GuildID               : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(64), unique = True, index = True, nullable = False)
    CommandPrefixDND      : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(16), default = "&", nullable = False)
    CommandPrefixTraveller: ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(16), default = "!", nullable = False)
    RuleSetEnforcementMode: ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(32), default = "Standard", nullable = False)
    MacroMasterRoleID     : ORM.Mapped[str | None]        = ORM.mapped_column(SQLAlchemy.String(64), nullable = True)
    CreatedAt             : ORM.Mapped[DateTime.datetime] = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    UpdatedAt             : ORM.Mapped[DateTime.datetime] = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), onupdate = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
