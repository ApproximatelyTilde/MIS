import datetime        as DateTime
import typing          as Typing
import uuid            as UUID
import sqlalchemy      as SQLAlchemy
import sqlalchemy.orm  as ORM
import Server.Database as Database

class Alias(Database.Base):
    __tablename__ = "Aliases"
    ID             : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UUID.uuid4()))
    Name           : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(100), index = True, nullable = False)
    Content        : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.Text, nullable = False)
    Scope          : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(16), index = True, nullable = False)
    OwnerID        : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(64), index = True, nullable = False)
    ServerID       : ORM.Mapped[str | None]        = ORM.mapped_column(SQLAlchemy.String(64), index = True, nullable = True)
    CollaboratorIDs: ORM.Mapped[list[str]]         = ORM.mapped_column(SQLAlchemy.JSON, default = list, nullable = False)
    CreatedAt      : ORM.Mapped[DateTime.datetime] = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    UpdatedAt      : ORM.Mapped[DateTime.datetime] = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), onupdate = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)

class Snippet(Database.Base):
    __tablename__ = "Snippets"
    ID             : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UUID.uuid4()))
    Name           : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(100), index = True, nullable = False)
    Content        : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.Text, nullable = False)
    Scope          : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(16), index = True, nullable = False)
    OwnerID        : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(64), index = True, nullable = False)
    ServerID       : ORM.Mapped[str | None]        = ORM.mapped_column(SQLAlchemy.String(64), index = True, nullable = True)
    CollaboratorIDs: ORM.Mapped[list[str]]         = ORM.mapped_column(SQLAlchemy.JSON, default = list, nullable = False)
    CreatedAt      : ORM.Mapped[DateTime.datetime] = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    UpdatedAt      : ORM.Mapped[DateTime.datetime] = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), onupdate = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
