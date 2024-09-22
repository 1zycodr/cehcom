from pydantic import BaseModel


class LeadItemCreate(BaseModel):
    lead_id: int
    item_id: int
    quantity: int
    notion_uid: str
    notion_nid: int | None
    notion_lead_nid: int | None
    data_hash: str | None


class LeadItemUpdate(LeadItemCreate):
    id: int
