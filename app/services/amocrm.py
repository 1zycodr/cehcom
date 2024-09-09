from app.crud.schemas import LeadCreate
from app.repository.notion import NotionRepo
from app.repository.tgbot import Alert
from app.crud import lead as lead_crud
from app.schemas.lead import Lead


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
                uid = NotionRepo.get_template()
                if uid is None:
                    Alert.critical('`🛑 Создайте черновики лидов.`')
                    return
                else:
                    NotionRepo.update_lead(lead, uid)
                lead_crud.create(self.db, LeadCreate(amo_id=lead.id, notion_uid=uid, data_hash=lead.hash()))
            elif lead.hash() != db_lead.data_hash:
                NotionRepo.update_lead(lead, db_lead.notion_uid)
                lead_crud.update_hash(self.db, db_lead.id, lead.hash())
