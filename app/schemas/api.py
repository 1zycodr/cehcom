from pydantic import BaseModel


class LeadAddItemRequest(BaseModel):
    lead_id: int
    item_nid: str
