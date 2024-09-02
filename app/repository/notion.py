import os

import pytz
from notion_client import Client, APIResponseError
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv, set_key

from app.core import settings
from app.schemas.lead import Lead
from app.schemas.notion import *


class NotionRepo:
    items_db_id = 'f59c2429df1749979ea76509fcfcdb8c'
    lead_db_id = '5824aff3f4374a3787a37e5caa12d8e1'
    updated_at_key = 'LAST_UPDATED_AT'
    timezone = pytz.timezone('Asia/Almaty')

    client = Client(auth=settings.NOTION_SECRET)

    @classmethod
    def load_updated_at(cls, update_all: bool = False) -> str:
        if update_all:
            updated_at = datetime.now(cls.timezone) - timedelta(days=365 * 3)
            return updated_at.strftime('%Y-%m-%dT%H:%M:%S.%f%Z')
        load_dotenv(find_dotenv())
        last_run_date = os.getenv(cls.updated_at_key)
        if last_run_date:
            return last_run_date
        else:
            updated_at = datetime.now(cls.timezone) - timedelta(days=365 * 3)
            return updated_at.strftime('%Y-%m-%dT%H:%M:%S.%f%Z')

    @classmethod
    def set_updated_at(cls, updated_at: datetime):
        set_key(
            '.env',
            cls.updated_at_key,
            updated_at.strftime('%Y-%m-%dT%H:%M:%S.%f%Z'),
        )

    @classmethod
    def get_items(cls, filter: dict) -> list[Item]:
        items = []
        kw = {}
        while True:
            resp = cls.client.databases.query(
                database_id=cls.items_db_id,
                filter=filter,
                **kw,
            )
            for item in resp.get('results', []):
                items.append(Item.from_response(item))
            print('Items loaded from Notion:', len(items))
            if not resp['has_more']:
                break
            kw['start_cursor'] = resp['next_cursor']
        return items

    @classmethod
    def get_item_by_id(cls, id: str) -> Item | None:
        try:
            resp = cls.client.pages.retrieve(id)
            return Item.from_response(resp)
        except APIResponseError:
            return None

    @classmethod
    def set_deleted(cls, item: Item):
        cls.client.pages.update(
            page_id=item.id,
            properties={
                'Каталог статус': {
                    'type': 'status',
                    'status': {'name': ItemStatus.off},
                },
            },
        )

    @classmethod
    def add_lead(cls, lead: Lead) -> str:
        result = cls.client.pages.create(
            parent={'database_id': cls.lead_db_id},
            icon={'external': {'url': 'https://www.notion.so/icons/timeline_lightgray.svg'}, 'type': 'external'},
            properties=lead.to_notion(),
        )
        return result['id']

    @classmethod
    def update_lead(cls, lead: Lead, uid: str):
        cls.client.pages.update(
            page_id=uid,
            properties=lead.to_notion_update(),
        )
