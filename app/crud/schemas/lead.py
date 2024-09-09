from pydantic import BaseModel


class LeadCreate(BaseModel):
    amo_id: int
    notion_uid: str
    data_hash: str


class LeadUpdate(LeadCreate):
    id: int
