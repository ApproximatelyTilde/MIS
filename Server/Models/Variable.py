import datetime        as DateTime
import typing          as Typing
import uuid            as UUID
import sqlalchemy      as SQLAlchemy
import sqlalchemy.orm  as ORM
import Server.Database as Database

class UserVariable(Database.Base):
    __tablename__ = "UserVariables"
    UserID   : ORM.Mapped[str]                  = ORM.mapped_column(SQLAlchemy.String(64), primary_key = True)
    Variables: ORM.Mapped[dict[str, Typing.Any]] = ORM.mapped_column(SQLAlchemy.JSON, default = dict, nullable = False)
    UpdatedAt: ORM.Mapped[DateTime.datetime]    = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), onupdate = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)

class ServerVariable(Database.Base):
    __tablename__ = "ServerVariables"
    GuildID  : ORM.Mapped[str]                  = ORM.mapped_column(SQLAlchemy.String(64), primary_key = True)
    Variables: ORM.Mapped[dict[str, Typing.Any]] = ORM.mapped_column(SQLAlchemy.JSON, default = dict, nullable = False)
    UpdatedAt: ORM.Mapped[DateTime.datetime]    = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), onupdate = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)

class GlobalVariable(Database.Base):
    __tablename__ = "GlobalVariables"
    ID       : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UUID.uuid4()))
    Content  : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.Text, nullable = False)
    Name     : ORM.Mapped[str | None]        = ORM.mapped_column(SQLAlchemy.String(128), nullable = True)
    OwnerID  : ORM.Mapped[str | None]        = ORM.mapped_column(SQLAlchemy.String(64), index = True, nullable = True)
    CreatedAt: ORM.Mapped[DateTime.datetime] = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    UpdatedAt: ORM.Mapped[DateTime.datetime] = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), onupdate = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
