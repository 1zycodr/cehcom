from sqlalchemy import Column, DateTime, func
from app.crud.models.base import Base


class DeleteMixin(Base):
    __abstract__ = True
    deleted_at = Column(DateTime, nullable=True)


class CreatedAtMixin(Base):
    __abstract__ = True
    created_at = Column(DateTime,
                        nullable=False,
                        server_default=func.now())
