from ._crud import CRUDBase
from .models.lead import Lead
from .schemas import LeadCreate, LeadUpdate


class CRUDLead(CRUDBase[Lead, LeadCreate, LeadUpdate]):

    def get_by_amo_id(self, db, amo_id) -> Lead | None:
        return db.query(self.model).filter(
            self.model.amo_id == amo_id,
        ).first()


lead = CRUDLead(Lead)
