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
            if db_lead is None:  # создаем лида из черновика
                uid = NotionRepo.get_lead_template()
                if uid is None:
                    Alert.critical('`🛑 Создайте черновики п-сделок!`')
                    return
                else:
                    notion_item = NotionRepo.update_lead(lead, uid)
                lead_crud.create(self.db, LeadCreate(amo_id=lead.id, notion_uid=uid, data_hash=lead.hash()))
                AmoRepo.update_lead_fields(lead.id, notion_item.to_amo_update(lead.id))
                self._load_lead_items(lead.id)
            elif lead.hash() != db_lead.data_hash:  # обновляем лида если изменены данные
                lead_crud.update_hash(self.db, db_lead.id, lead.hash())
                NotionRepo.update_lead(lead, db_lead.notion_uid)

    def _load_lead_items(self, lead_id: int):
        db_lead_items = dict(lead_item_crud.get_by_lead_id(self.db, lead_id))
        amo_lead_items, _, _ = AmoRepo.get_lead_items_ids(lead_id)
        create_items_ids, update_items_ids = [], []
        for amo_item_id, amo_item_quantity in amo_lead_items:
            if amo_item_id in db_lead_items:
                update_items_ids.append(amo_item_id)
            else:
                create_items_ids.append(amo_item_id)
        create_items = AmoRepo.get_lead_products(create_items_ids)
        update_items = AmoRepo.get_lead_products(update_items_ids)
        self.process_dt_products_update(create_items, update_items)

    def sync_lead_items(self, lead_id: int):
        amo_items, _, _ = AmoRepo.get_lead_items_ids(lead_id)
        current_items = lead_item_crud.get_by_lead_id_with_uid(self.db, lead_id)
        amo_items = dict(amo_items)
        for item_id, quantity, uid in current_items:
            amo_quantity = amo_items.get(item_id, None)
            if amo_quantity is not None:
                if amo_quantity != quantity:
                    NotionRepo.update_quantity(uid, int(amo_quantity))
                    lead_item_crud.update_quantity(self.db, lead_id, item_id, int(amo_quantity))
            else:
                # отвязать от лида - для удаления
                pass

    def process_dt_products_update(self,
                                   added: list[AMODTProduct],
                                   updated: list[AMODTProduct]):
        # создание новых товаров сделки
        for item in added:
            lead_id = item.lead_id()
            if lead_id == 0:
                continue
            # проверка присутствия в бд лида
            db_lead = lead_crud.get_by_amo_id(self.db, lead_id)
            if db_lead is None:
                continue
            # проверка присутствия в бд айтема
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
                item, uid, notion_item_id, notion_item_lead_id, lead_uid, quantity
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
            pass  # TODO обновление товаров
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
