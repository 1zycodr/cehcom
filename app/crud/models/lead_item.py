from sqlalchemy import Column, Integer, String, BigInteger

from .mixin import CreatedAtMixin


class LeadItem(CreatedAtMixin):
    __tablename__ = 'lead_item'

    lead_id = Column(
        BigInteger,
        primary_key=True,
        index=True,
        nullable=False,
    )
    item_id = Column(
        BigInteger,
        primary_key=True,
        index=True,
        nullable=False,
    )
    quantity = Column(
        Integer,
        nullable=False,
        default=0,
    )
    notion_uid = Column(
        String,
        nullable=False,
    )
    data_hash = Column(
        String,
        nullable=False,
    )
    notion_nid = Column(
        String,
        nullable=True,
    )
    notion_lead_nid = Column(
        String,
        nullable=True,
    )
