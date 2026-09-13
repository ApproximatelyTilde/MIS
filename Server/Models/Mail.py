import datetime        as DateTime
import enum            as Enumeration
import typing          as Typing
import uuid            as UUID
import sqlalchemy      as SQLAlchemy
import sqlalchemy.orm  as ORM
import Server.Database as Database

class MailCategory(str, Enumeration.Enum):
    SystemAlert     = "SystemAlert"
    CharacterReview = "CharacterReview"
    StoryNotice     = "StoryNotice"
    Administrative  = "Administrative"
    GeneralMessage  = "GeneralMessage"

class MailMessage(Database.Base):
    __tablename__ = "MailMessages"

    ID               : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UUID.uuid4()))
    SenderUserID     : ORM.Mapped[str | None]               = ORM.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Users.ID", ondelete = "SET NULL"), nullable = True, index = True)
    RecipientUserID  : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Users.ID", ondelete = "CASCADE"), nullable = False, index = True)
    Subject          : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.String(200), nullable = False)
    Body             : ORM.Mapped[str]                      = ORM.mapped_column(SQLAlchemy.Text, nullable = False)
    Category         : ORM.Mapped[MailCategory]             = ORM.mapped_column(SQLAlchemy.Enum(MailCategory, name = "MailCategory"), default = MailCategory.SystemAlert, nullable = False)
    RelatedEntityType: ORM.Mapped[str | None]               = ORM.mapped_column(SQLAlchemy.String(50), nullable = True)
    RelatedEntityID  : ORM.Mapped[str | None]               = ORM.mapped_column(SQLAlchemy.String(36), nullable = True)
    IsAutomated      : ORM.Mapped[bool]                     = ORM.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False, index = True)
    IsRead           : ORM.Mapped[bool]                     = ORM.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False, index = True)
    ParentMessageID  : ORM.Mapped[str | None]               = ORM.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("MailMessages.ID", ondelete = "SET NULL"), nullable = True)
    CreatedAt        : ORM.Mapped[DateTime.datetime]        = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    UpdatedAt        : ORM.Mapped[DateTime.datetime]        = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), onupdate = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    Sender           = ORM.relationship("User", foreign_keys = [SenderUserID], back_populates = "SentMail")
    Recipient        = ORM.relationship("User", foreign_keys = [RecipientUserID], back_populates = "ReceivedMail")
    ParentMessage    = ORM.relationship("MailMessage", remote_side = [ID], back_populates = "Replies")
    Replies          = ORM.relationship("MailMessage", back_populates = "ParentMessage")

