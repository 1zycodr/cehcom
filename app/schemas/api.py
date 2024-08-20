from pydantic import BaseModel


class LeadAddItemRequest(BaseModel):
    lead_id: int
    item_nid: str
    name: str
    size: str
    price: str
    quantity: str
    description: str
