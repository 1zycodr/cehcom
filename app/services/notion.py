from copy import deepcopy

import pytz
from notion_client import Client
from datetime import datetime

from app.core import settings
from app.schemas.notion import *
from ..core.config import red
from ..repository.amocrm import AmoRepo
from ..repository.notion import NotionRepo
from ..repository.tgbot import Alert


class NotionService:
    notion_repo: NotionRepo = NotionRepo()
    amo_repo: AmoRepo = AmoRepo()
    client = Client(auth=settings.NOTION_SECRET)
    timezone = pytz.timezone('Asia/Almaty')

    @classmethod
    def load_updated_from_notion(cls, update_all: bool = False) -> list[Item]:
        updated_at = cls.notion_repo.load_updated_at(update_all)
        print('Updated at:', updated_at)
        filter = {
            "and": [
                {
                    "property": "Каталог статус",
                    "status": {
                        "does_not_equal": ItemStatus.off,
                    },
                },
                {
                    "property": "Last edited time",
                    "last_edited_time": {
                        "on_or_after": updated_at,
                    },
                },
            ],
        }
        time_start = datetime.now(cls.timezone)
        items = cls.notion_repo.get_items(filter)
        print('Items loaded from Notion:', len(items))
        print('Time elapsed:', datetime.now(cls.timezone) - time_start)
        return items

    @classmethod
    def sync_with_amo(cls, update_all: bool = False):
        try:
            if update_all:
                Alert.info('`🔄 Полная синхронизация каталога в amoCRM...`')
            print('start sync', update_all)
            time_start = datetime.now(cls.timezone)
            items = cls.load_updated_from_notion(update_all)
            amo_items = cls.amo_repo.get_all_products()
            amo_items_ids = {
                amo_item.nid: amo_item
                for amo_item in amo_items
            }

            items_for_update = []
            items_for_delete = []
            items_for_create = []
            items_for_update_status_off = []

            for i, item in enumerate(items):
                if item.nid not in amo_items_ids:
                    if item.catalog_status != ItemStatus.delete:
                        items_for_create.append(deepcopy(item))
                    else:
                        items_for_update_status_off.append(deepcopy(item))
                    continue
                amo_item = amo_items_ids[item.nid]
                item.amo_id = amo_item.amo_id
                if item.catalog_status == ItemStatus.delete:
                    item.catalog_status = ItemStatus.off
                    items_for_delete.append(deepcopy(item))
                else:
                    items_for_update.append(deepcopy(item))

                # if item.catalog_status != ItemStatus.delete:
                #     items_for_create.append(deepcopy(item))
                # else:
                #     items_for_update_status_off.append(deepcopy(item))

            # обработка тех которые надо удалить
            cls.amo_repo.patch_items(items_for_delete)
            items_for_update_status_off.extend(items_for_delete)

            # проставляем статусы "удалено" в notion
            for item in items_for_update_status_off:
                cls.notion_repo.set_deleted(item)

            # создание новых
            cls.amo_repo.add_products(items_for_create)

            # обновление старых
            # сначала ищем связанные карточки в notion
            items_for_update.extend(cls.enrich_updated_items(items, items_for_update))
            cls.amo_repo.patch_items(items_for_update)

            # сохраняем время последнего обновления
            time_finish = datetime.now(cls.timezone)
            cls.notion_repo.set_updated_at(time_finish)

            print('Time elapsed:', time_finish - time_start)
            print('Updated:', len(items_for_update))
            print('Created:', len(items_for_create))
            print('Deleted:', len(items_for_delete))

            red.delete('sync-running')
            if update_all:
                Alert.info('`✅ Полная синхронизация каталога в amoCRM успешно завершена`')
        except Exception as ex:
            Alert.critical(f'`❌ Ошибка синхронизации с amoCRM:\n\n{ex}`')

    @classmethod
    def enrich_updated_items(cls, items: list[Item], updated_items: list[Item]) -> list[Item]:
        new_items = []
        items_ids = [item.id for item in items]
        for item in updated_items:
            if item.linked_ids is not None:
                for id in item.linked_ids:
                    if id not in items_ids:
                        itm = cls.notion_repo.get_item_by_id(id)
                        amo_itm = cls.amo_repo.get_product_by_nid(itm.nid)
                        if amo_itm is None:
                            continue
                        itm.amo_id = amo_itm.amo_id
                        if itm is not None and itm.catalog_status != ItemStatus.off:
                            new_items.append(itm)
        return new_items
