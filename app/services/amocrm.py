from app.crud.schemas import LeadCreate, LeadItemCreate
from app.repository.amocrm import AmoRepo
from app.repository.notion import NotionRepo
from app.repository.tgbot import Alert
from app.crud import (
    lead as lead_crud,
    lead_item as lead_item_crud,
)
from app.schemas import AMODTProduct
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
                uid = NotionRepo.get_lead_template()
                if uid is None:
                    Alert.critical('`🛑 Создайте черновики п-сделок!`')
                    return
                else:
                    notion_item = NotionRepo.update_lead(lead, uid)
                lead_crud.create(self.db, LeadCreate(amo_id=lead.id, notion_uid=uid, data_hash=lead.hash()))
                AmoRepo.update_lead_fields(lead.id, notion_item.to_amo_update(lead.id))
            elif lead.hash() != db_lead.data_hash:
                lead_crud.update_hash(self.db, db_lead.id, lead.hash())
                NotionRepo.update_lead(lead, db_lead.notion_uid)

    def sync_lead_items(self, lead_id: int):
        update_items = AmoRepo.get_lead_items_ids(lead_id)
        current_items = lead_item_crud.get_by_lead_id(self.db, lead_id)
        if update_items != current_items:
            pass

    def process_dt_products_update(self,
                                   added: list[AMODTProduct],
                                   updated: list[AMODTProduct]):
        # создание новых товаров сделки
        for item in added:
            lead_id = item.lead_id()
            if lead_id == 0:
                continue
            # проверка присутствия в бд
            db_lead_items = lead_item_crud.get_by_lead_id(self.db, lead_id)
            db_lead_items = dict(db_lead_items)
            # если есть - переносим в обновление
            if item.id in db_lead_items:
                updated.append(item)
                continue

            uid, notion_item_id = NotionRepo.get_lead_item_template()
            if uid is None or notion_item_id is None:
                Alert.critical('`🛑 Создайте черновики п-заказов!`')
                continue

            # запрашиваем quantity и айди лида ноушена товара
            quantity = None
            amo_lead_items, notion_item_lead_id, lead_uid = AmoRepo.get_lead_items_ids(lead_id)
            for amo_item_id, amo_item_quantity in amo_lead_items:
                if amo_item_id == item.id:
                    quantity = amo_item_quantity
                    break
            if quantity is None:
                continue

            # добавляем п-заказ в notion
            notion_item = NotionRepo.update_lead_item(
                item, uid, notion_item_id, notion_item_lead_id, lead_uid
            )
            # сохраняем в базу
            lead_item_crud.create(
                self.db,
                LeadItemCreate(
                    lead_id=lead_id,
                    item_id=item.id,
                    quantity=quantity,
                    notion_uid=uid,
                ),
            )
            # обновляем товар в амо
            AmoRepo.update_lead_item_after_creation(
                item.id, notion_item.to_amo_update(item.id))

        # обновление товаров сделки
        for item in updated:
            pass
            # lead_id = item.lead_id()
            # if lead_id == 0:
            #     continue
            # # проверка присутствия в бд
            # db_lead_items = lead_item_crud.get_by_lead_id(self.db, lead_id)
            # db_lead_items = dict(db_lead_items)
            # # если есть - переносим в обновление
            # if item.id in db_lead_items:
            #     updated.append(item)
            #     continue
