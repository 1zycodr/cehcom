from ._crud import CRUDBase
from .models.lead_item import LeadItem
from .schemas import LeadItemCreate, LeadItemUpdate
from ..core.db import SessionLocal


class CRUDLeadItem(CRUDBase[LeadItem, LeadItemCreate, LeadItemUpdate]):

    def get_by_lead_id(self, db: SessionLocal, lead_id: int) -> list[(int, int)]:
        data = db.query(
            self.model.item_id,
            self.model.quantity,
        ).filter(
            self.model.lead_id == lead_id,
        ).all()
        return data


lead_item = CRUDLeadItem(LeadItem)
