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

    def get_by_lead_id_with_uid(self, db: SessionLocal, lead_id: int) -> list[(int, int, str)]:
        data = db.query(
            self.model.item_id,
            self.model.quantity,
            self.model.notion_uid,
        ).filter(
            self.model.lead_id == lead_id,
        ).all()
        return data

    def update_quantity(self, db: SessionLocal, lead_id: int, item_id: int, quantity: int):
        db.query(self.model).filter(
            self.model.lead_id == lead_id,
            self.model.item_id == item_id,
        ).update(
            {'quantity': quantity},
        )
        db.commit()


lead_item = CRUDLeadItem(LeadItem)
