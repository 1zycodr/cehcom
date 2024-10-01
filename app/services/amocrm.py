import time

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
        current_items = dict(current_items)
        add_items_ids = []
        update_items_ids = []
        for item_id, quantity in amo_items.items():
            curr_quantity, current_item_uid = current_items.get(item_id, (None, None))
            if current_item_uid is not None:
                if curr_quantity != quantity:
                    NotionRepo.update_quantity(current_item_uid, int(quantity))
                    lead_item_crud.update_quantity(self.db, lead_id, item_id, quantity)
                update_items_ids.append(int(item_id))
            else:
                add_items_ids.append(int(item_id))
        for item_id, pair in current_items.items():
            _, uid = pair
            if item_id not in amo_items:
                NotionRepo.unlink_item_from_lead(uid)
        create_items = AmoRepo.get_lead_products(add_items_ids)
        update_items = AmoRepo.get_lead_products(update_items_ids)
        self.process_dt_products_update(
            create_items,
            update_items,
            check_hash=False,
        )

    def process_dt_products_update(self,
                                   added: list[AMODTProduct],
                                   updated: list[AMODTProduct],
                                   deleted: list[int] | None = None,
                                   check_hash: bool = True):
        # создание новых товаров сделки
        if len(added) > 0:  # если создались новые товары - ждём 2с обновления количества
            time.sleep(2)
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

            uid, notion_item_id, notion_item_nid = NotionRepo.get_lead_item_template()
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
                item, uid, notion_item_id, notion_item_lead_id, lead_uid, quantity, notion_item_nid
            )
            # сохраняем в базу
            lead_item_crud.create(
                self.db,
                LeadItemCreate(
                    lead_id=lead_id,
                    item_id=item.id,
                    quantity=quantity,
                    notion_uid=uid,
                    notion_nid=notion_item_id,
                    notion_lead_nid=notion_item_lead_id,
                    data_hash=item.hash(),
                ),
            )
            # обновляем товар в амо
            AmoRepo.update_lead_item_after_creation(
                item.id, notion_item.to_amo_update(item.id))

        # обновление товаров сделки из amo -> notion
        for item in updated:
            lead_id = item.lead_id()
            if lead_id == 0:
                continue
            # проверка присутствия в бд
            db_lead_item = lead_item_crud.get_by_lead_id_item_id(self.db, lead_id, item.id)
            if db_lead_item is None:
                continue
            # проверяем хеш
            if check_hash and db_lead_item.data_hash == item.hash():
                continue
            # обновление в notion с lead_uid
            lead_uid = lead_crud.get_uid_by_amo_id(self.db, lead_id)
            NotionRepo.update_lead_item_partial(item, db_lead_item, lead_uid)
            # сохранение хеша
            lead_item_crud.update_hash(self.db, db_lead_item.lead_id, db_lead_item.item_id, item.hash())
            print('Updated lead item:', item.id)

        if deleted is not None:
            items = lead_item_crud.get_by_item_ids(self.db, deleted)
            for item in items:
                NotionRepo.archive(item.notion_uid)
                print('Archived lead item:', item.item_id)
            lead_item_crud.delete_by_item_ids(self.db, deleted)
