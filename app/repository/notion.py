import os

import pytz
from notion_client import Client, APIResponseError
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv, set_key

from app.core import settings
from app.schemas.lead import Lead, LeadUpdate
from app.schemas.notion import *


class NotionRepo:
    items_db_id = 'f59c2429df1749979ea76509fcfcdb8c'
    lead_db_id = '5824aff3f4374a3787a37e5caa12d8e1'
    updated_at_key = 'LAST_UPDATED_AT'
    lead_updated_at_key = 'LAST_UPDATED_AT_LEADS'
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
    def load_updated_at_leads(cls, update_all: bool = False) -> str:
        if update_all:
            updated_at = datetime.now(cls.timezone) - timedelta(days=365 * 3)
            return updated_at.strftime('%Y-%m-%dT%H:%M:%S.%f%Z')
        load_dotenv(find_dotenv())
        last_run_date = os.getenv(cls.lead_updated_at_key)
        if last_run_date:
            return last_run_date
        else:
            updated_at = datetime.now(cls.timezone) - timedelta(days=365 * 3)
            return updated_at.strftime('%Y-%m-%dT%H:%M:%S.%f%Z')

    @classmethod
    def set_updated_at_leads(cls, updated_at: datetime):
        set_key(
            '.env',
            cls.lead_updated_at_key,
            updated_at.strftime('%Y-%m-%dT%H:%M:%S.%f%Z'),
        )

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
    def get_template(cls) -> str | None:
        resp = cls.client.databases.query(
            database_id=cls.lead_db_id,
            filter={
                'property': 'Статус сделки',
                'status': {
                    'equals': 'Черновик'
                }
            },
            page_size=1
        )
        try:
            return resp.get('results', [{'id': None}])[0].get('id')
        except IndexError:
            return None

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
        print('Updating lead:', lead.id)
        cls.client.pages.update(
            page_id=uid,
            properties=lead.to_notion_update(),
        )

    @classmethod
    def get_leads(cls, filter: dict) -> list[LeadUpdate]:
        leads = []
        kw = {}
        while True:
            resp = cls.client.databases.query(
                database_id=cls.lead_db_id,
                filter=filter,
                **kw,
            )
            for item in resp.get('results', []):
                leads.append(LeadUpdate.from_notion_resp(item))
            print('Leads loaded from Notion:', len(leads))
            if not resp['has_more']:
                break
            kw['start_cursor'] = resp['next_cursor']
        return leads

    @classmethod
    def load_updated_leads(cls, update_all: bool = False) -> list[LeadUpdate]:
        updated_at = cls.load_updated_at_leads(update_all)
        filter = {
            'and': [
                {
                    'property': 'Last edited time',
                    'date': {
                        'on_or_after': updated_at,
                    },
                },
                # {
                #     'property': 'Name',
                #     'title': {
                #         'equals': 'Амирлан Лид',
                #     },
                # },
            ],
        }
        time_start = datetime.now(cls.timezone)
        leads = cls.get_leads(filter)
        print('Leads loaded from Notion:', len(leads))
        print('Time elapsed:', datetime.now(cls.timezone) - time_start)
        cls.set_updated_at_leads(time_start)
        return leads
