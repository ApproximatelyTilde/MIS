import datetime        as DateTime
import typing          as Typing
import uuid            as UUID
import sqlalchemy      as SQLAlchemy
import sqlalchemy.orm  as ORM
import Server.Database as Database

class CombatEncounter(Database.Base):
    __tablename__ = "CombatEncounters"
    ID                  : ORM.Mapped[str]                         = ORM.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UUID.uuid4()))
    ChannelID           : ORM.Mapped[str]                         = ORM.mapped_column(SQLAlchemy.String(64), unique = True, index = True, nullable = False)
    GuildID             : ORM.Mapped[str | None]                  = ORM.mapped_column(SQLAlchemy.String(64), index = True, nullable = True)
    RoundNumber         : ORM.Mapped[int]                         = ORM.mapped_column(SQLAlchemy.Integer, default = 1, nullable = False)
    ActiveCombatantIndex: ORM.Mapped[int]                         = ORM.mapped_column(SQLAlchemy.Integer, default = 0, nullable = False)
    Combatants          : ORM.Mapped[list[dict[str, Typing.Any]]] = ORM.mapped_column(SQLAlchemy.JSON, default = list, nullable = False)
    ActiveEffects       : ORM.Mapped[list[dict[str, Typing.Any]]] = ORM.mapped_column(SQLAlchemy.JSON, default = list, nullable = False)
    IsActive            : ORM.Mapped[bool]                        = ORM.mapped_column(SQLAlchemy.Boolean, default = True, nullable = False, index = True)
    CreatedAt           : ORM.Mapped[DateTime.datetime]           = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    UpdatedAt           : ORM.Mapped[DateTime.datetime]           = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), onupdate = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
