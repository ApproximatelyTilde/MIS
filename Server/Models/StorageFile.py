import datetime        as DateTime
import sqlalchemy      as SQLAlchemy
import sqlalchemy.orm  as ObjectRelationalMapper
import uuid            as UniversallyUniqueIdentifier
import Server.Database as Database

class StorageFile(Database.Base):
    __tablename__ = "StorageFiles"
    Identifier     : ObjectRelationalMapper.Mapped[str]               = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), primary_key = True, default = lambda: str(UniversallyUniqueIdentifier.uuid4()))
    OwnerIdentifier: ObjectRelationalMapper.Mapped[str]               = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(36), SQLAlchemy.ForeignKey("Users.Identifier", ondelete = "CASCADE"), nullable = False, index = True)
    FileName       : ObjectRelationalMapper.Mapped[str]               = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(255), nullable = False)
    ContentType    : ObjectRelationalMapper.Mapped[str]               = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(100), nullable = False)
    FileSizeBytes  : ObjectRelationalMapper.Mapped[int]               = ObjectRelationalMapper.mapped_column(SQLAlchemy.BigInteger, nullable = False)
    ObjectKey      : ObjectRelationalMapper.Mapped[str]               = ObjectRelationalMapper.mapped_column(SQLAlchemy.String(500), nullable = False, unique = True)
    IsPublic       : ObjectRelationalMapper.Mapped[bool]              = ObjectRelationalMapper.mapped_column(SQLAlchemy.Boolean, default = False, nullable = False)
    CreatedAt      : ObjectRelationalMapper.Mapped[DateTime.datetime] = ObjectRelationalMapper.mapped_column(SQLAlchemy.DateTime(timezone = True), default = DateTime.datetime.utcnow, nullable = False)
    Owner = ObjectRelationalMapper.relationship("User", back_populates = "StorageFiles")
