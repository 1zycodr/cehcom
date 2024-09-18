from pydantic import BaseModel


class LeadItemCreate(BaseModel):
    lead_id: int
    item_id: int
    quantity: int
    notion_uid: str


class LeadItemUpdate(LeadItemCreate):
    id: int
