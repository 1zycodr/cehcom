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
from ..repository.wordpress import WordpressRepository


class NotionService:
    notion_repo: NotionRepo = NotionRepo()
    amo_repo: AmoRepo = AmoRepo()
    wp_repo: WordpressRepository = WordpressRepository()
    client = Client(auth=settings.NOTION_SECRET)
    timezone = pytz.timezone('Asia/Almaty')

    @classmethod
    def load_updated_from_notion(cls, update_all: bool = False) -> list[Item]:
        updated_at = cls.notion_repo.load_updated_at(update_all)
        print('load_updated_from_notion', updated_at)
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
                {
                    'property': 'NID',
                    'formula': {
                        'string': {
                            'equals': '02034',
                        }
                    },
                }
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

            amo_items = []
            wp_items = []
            if len(items) != 0:
                amo_items = cls.amo_repo.get_all_products()
                wp_items = cls.wp_repo.get_all_products()

            amo_items_ids = {
                amo_item.nid: amo_item
                for amo_item in amo_items
            }

            wp_items_ids = {
                wp_item.nid: wp_item
                for wp_item in wp_items
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

            if len(items) != 0:
                # обработка тех которые надо удалить
                items_for_delete, items_for_update, items_for_update_status_off = cls.enrich_deleted_items(
                    items_for_delete,
                    items_for_update,
                    items_for_update_status_off,
                )
                cls.amo_repo.delete_from_catalog([i.amo_id for i in items_for_delete])
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

            if update_all:
                Alert.info('`✅ Полная синхронизация каталога в amoCRM успешно завершена`')
        except Exception as ex:
            Alert.critical(f'`❌ Ошибка синхронизации каталога с amoCRM:\n\n{ex}`')
        red.delete('sync-running')

    @classmethod
    def sync_leads(cls, update_all: bool = False):
        try:
            if update_all:
                Alert.info_lead('`🔄 Полная синхронизация лидов в amoCRM...`')
            print('start sync leads', update_all)
            time_start = datetime.now(cls.timezone)

            leads = cls.notion_repo.load_updated_leads(update_all)

            update_leads = []
            for lead in leads:
                old_hash = red.get(f'sync-notion-lead-hash-{lead.id}')
                new_hash = lead.hash()
                if old_hash is not None:
                    if old_hash.decode('utf-8') == new_hash:
                        continue
                red.set(f'sync-notion-lead-hash-{lead.id}', new_hash)
                update_leads.append(lead)

            print('updating leads:', [lead.id for lead in update_leads])
            if len(update_leads) != 0:
                AmoRepo.update_leads(leads)

            time_finish = datetime.now(cls.timezone)
            print('finish sync leads, time elapsed:', time_finish - time_start)

            if update_all:
                Alert.info_lead('`✅ Полная синхронизация лидов в amoCRM успешно завершена`')

        except Exception as ex:
            Alert.critical(f'`❌ Ошибка синхронизации лидов с amoCRM:\n\n{ex}`')
        red.delete('sync-leads-running')

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

    @classmethod
    def enrich_deleted_items(cls,
                             items_for_delete: list[Item],
                             items_for_update: list[Item],
                             items_for_update_status_off: list[Item],
                             ) -> tuple[list[Item], list[Item], list[Item]]:
        # добавляем подтовары в списки удаления и обновления статусов
        new_items_for_delete = []
        for item in items_for_delete:
            if item.subproducts_ids is not None:
                for id in item.linked_ids:
                    sub_itm = cls.notion_repo.get_item_by_id(id)
                    if sub_itm is not None:
                        amo_itm = cls.amo_repo.get_product_by_nid(sub_itm.nid)
                        if amo_itm is not None:
                            sub_itm.amo_id = amo_itm.amo_id
                            new_items_for_delete.append(sub_itm)
        items_for_delete.extend(new_items_for_delete)

        # # добавляем в обновление статусов
        # items_for_update_status_off.extend(new_items_for_delete)

        # исключаем подтовары из списков на обновление
        new_items_for_update = []
        ids = [i.nid for i in new_items_for_delete]
        for item in items_for_update:
            if item.nid not in ids:
                new_items_for_update.append(item)
        return items_for_delete, new_items_for_update, items_for_update_status_off