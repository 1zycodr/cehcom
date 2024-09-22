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

    def get_by_lead_id_item_id(self, db: SessionLocal, lead_id: int, item_id: int) -> LeadItem:
        data = db.query(
            self.model,
        ).filter(
            self.model.lead_id == lead_id,
            self.model.item_id == item_id,
        ).first()
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

    def update_hash(self, db: SessionLocal, lead_id: int, item_id: int, data_hash: str):
        db.query(self.model).filter(
            self.model.lead_id == lead_id,
            self.model.item_id == item_id,
        ).update(
            {'data_hash': data_hash},
        )
        db.commit()

    def get_by_item_ids(self, db: SessionLocal, item_ids: list[int]) -> list[LeadItem]:
        if len(item_ids) == 0:
            return []
        data = db.query(
            self.model,
        ).filter(
            self.model.item_id.in_(item_ids),
        ).all()
        return data

    def delete_by_item_ids(self, db: SessionLocal, item_ids: list[int]):
        db.query(self.model).filter(
            self.model.item_id.in_(item_ids),
        ).delete(synchronize_session=False)
        db.commit()


lead_item = CRUDLeadItem(LeadItem)
