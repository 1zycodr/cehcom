from sqlalchemy import Column, Integer, String, BigInteger

from .mixin import CreatedAtMixin


class Lead(CreatedAtMixin):
    __tablename__ = 'lead'

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
    )
    amo_id = Column(
        BigInteger,
        nullable=False,
        unique=True,
    )
    notion_uid = Column(
        String,
        nullable=True,
    )
