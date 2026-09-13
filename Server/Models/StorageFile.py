import datetime        as DateTime
import sqlalchemy      as SQLAlchemy
import sqlalchemy.orm  as ORM
import uuid            as UUID
import Server.Database as Database

class StorageFile(Database.Base):
    __tablename__ = "StorageFiles"
    ID           : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UUID.uuid4()))
    OwnerID      : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Users.ID", ondelete = "CASCADE"), nullable = False, index = True)
    FileName     : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(255), nullable = False)
    ContentType  : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(100), nullable = False)
    FileSizeBytes: ORM.Mapped[int]               = ORM.mapped_column(SQLAlchemy.BigInteger, nullable = False)
    ObjectKey    : ORM.Mapped[str]               = ORM.mapped_column(SQLAlchemy.String(500), nullable = False, unique = True)
    IsPublic     : ORM.Mapped[bool]              = ORM.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False)
    CreatedAt    : ORM.Mapped[DateTime.datetime] = ORM.mapped_column(SQLAlchemy.DateTime(timezone = True), default = lambda: DateTime.datetime.now(DateTime.UTC), nullable = False)
    Owner = ORM.relationship("User", back_populates = "StorageFiles")
