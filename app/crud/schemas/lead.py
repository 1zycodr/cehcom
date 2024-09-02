from pydantic import BaseModel


class LeadCreate(BaseModel):
    amo_id: int
    notion_uid: str


class LeadUpdate(LeadCreate):
    id: int
