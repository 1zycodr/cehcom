from app.crud.schemas import LeadCreate
from app.repository.notion import NotionRepo
from app.schemas.lead import Lead
from app.crud import lead as lead_crud


class AMOService:

    def __init__(self, db):
        self.db = db

    def process_lead_update_hook(self, lead: Lead):
        # смотрим заполнено ли поле сделки "П-статус"
        #   смотрим есть ли сделка в бд
        #       если нет:
        #           создаем в notion
        #           добавляем в бд
        #       иначе:
        #           обновляем в notion
        #
        if lead.p_status() is not None:
            db_lead = lead_crud.get_by_amo_id(self.db, lead.id)
            if db_lead is None:
                uid = NotionRepo.add_lead(lead)
                lead_crud.create(self.db, LeadCreate(amo_id=lead.id, notion_uid=uid))
            else:
                NotionRepo.update_lead(lead, db_lead.notion_uid)
