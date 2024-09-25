from __future__ import annotations

import hashlib
import json

import requests

from datetime import datetime, timezone

from pydantic import BaseModel, model_validator

from .api import LeadAddItemRequest
from .lead import build_nested_dict
from .notion import Item, ItemStatus


class NotionDTProduct(BaseModel):
    id: str
    notion_pz_nid: str

    @model_validator(mode='before')
    def extract_fields(self: dict, *args, **kwargs) -> dict:
        self['id'] = str(self.get('id', ''))
        self['notion_pz_nid'] = str(self.get('properties', {})
                                     .get('ID П-заказа', {})
                                     .get('unique_id', {})
                                     .get('number', 0))
        return self

    def to_amo_update(self, item_id: int) -> dict:
        return {
            'id': item_id,
            'custom_fields_values': [
                {
                    'field_id': 1450233,  # пз нид
                    'values': [
                        {
                            'value': f'PZ-{self.notion_pz_nid}',
                        },
                    ],
                },
                {
                    'field_id': 1450235,  # uid
                    'values': [
                        {
                            'value': self.id,
                        },
                    ],
                },
                {
                    'field_id': 1450237,  # uid
                    'values': [
                        {
                            'value': f'https://www.notion.so/cehcom/{self.id.replace('-', '')}',
                        },
                    ],
                },
            ],
        }


class AMODTProduct(BaseModel):
    id: int = 0
    name: str = ''
    description: str = ''
    custom_fields_values: list[dict]

    def hash(self) -> str:
        dict_str = json.dumps(self.dict(), sort_keys=True)
        return hashlib.md5(dict_str.encode('utf-8')).hexdigest()

    def lead_id(self) -> int:
        for field in self.custom_fields_values:
            if int(field['field_id']) == 1450239:
                try:
                    return int(field['values'][0]['values'][0]['value'])
                except KeyError:
                    return int(field['values'][0]['value'])
        return 0

    def to_notion_partial_update(self,
                                 item_notion_id: str | int,
                                 item_notion_lead_id: str | int,
                                 item_notion_lead_uid: str) -> dict:
        result = {
            'Name': {
                'title': [
                    {
                        'text': {
                            'content': f'ПЗ-{item_notion_id}-{item_notion_lead_id} / {self.name}',
                        }
                    },
                ],
            },
            'Цена агент': {
                'number': self.get_agent_price(),
            },
            'Описание из amo': {
                'rich_text': [
                    {
                        'text': {
                            'content': self.get_description(),
                        }
                    }
                ]
            },
            'Цена': {
                'number': self.get_price(),
            },
            'Размеры из амо': {
                'rich_text': [
                    {
                        'text': {
                            'content': self.get_sizes(),
                        }
                    }
                ]
            },
            'Примечание': {
                'rich_text': [
                    {
                        'text': {
                            'content': self.get_note(),
                        }
                    }
                ]
            },
            'Для накладной шт': {
                'number': self.get_count_for_invoice(),
            },
            '🚇 Сделки в производстве': {
                'relation': [
                    {
                        'id': item_notion_lead_uid,
                    },
                ],
            },
        }
        return result

    def to_notion_update(self,
                         item_notion_id: str | int,
                         item_notion_lead_id: str | int,
                         lead_uid: str,
                         quantity: int) -> dict:
        result = {
            'Name': {
                'title': [
                    {
                        'text': {
                            'content': f'ПЗ-{item_notion_id}-{item_notion_lead_id} / {self.name}',
                        }
                    },
                ],
            },
            'Статус': {
                'status': {
                    'name': 'Не приступили',
                },
            },
            'Описание из amo': {
                'rich_text': [
                    {
                        'text': {
                            'content': self.get_description(),
                        }
                    }
                ]
            },
            'Цена': {
                'number': self.get_price(),
            },
            'Шт': {
                'number': quantity,
            },
            'Цена агент': {
                'number': self.get_agent_price(),
            },
            'Размеры из амо': {
                'rich_text': [
                    {
                        'text': {
                            'content': self.get_sizes(),
                        }
                    }
                ]
            },
            'Примечание': {
                'rich_text': [
                    {
                        'text': {
                            'content': self.get_note(),
                        }
                    }
                ]
            },
            'ID сделки amoCRM': {
                'number': self.lead_id(),
            },
            'ID товара amoCRM': {
                'number': self.id,
            },
            'Для накладной шт': {
                'number': self.get_count_for_invoice(),
            },
            '🚇 Сделки в производстве': {
                'relation': [
                    {
                        'id': lead_uid,
                    },
                ],
            },
            '💯 Товар': {
                'relation': [
                    {
                        'id': uid,
                    } for uid in self.get_notion_parent_uid()
                ],
            },
        }
        return result

    @classmethod
    def from_item(cls, item: Item, bt_item_id: int, body: LeadAddItemRequest) -> AMODTProduct:
        custom_fields = [
            {
                'field_id': 1450227,
                'values': [
                    {'value': item.photo},
                ],
            },
            {
                'field_id': 1450217,
                'values': [
                    {'value': str(bt_item_id)},
                ],
            },
            {
                'field_id': 1450219,
                'values': [
                    {'value': item.nid},
                ],
            },
            {
                'field_id': 1450229,
                'values': [
                    {'value': item.admin_link},
                ],
            },
            {
                'field_id': 1450231,
                'values': [
                    {'value': item.client_link},
                ],
            },
            {
                'field_id': 1450221,
                'values': [
                    {'value': item.id},
                ],
            },
            {
                'field_id': 1110357,
                'values': [
                    {'value': int(body.price)},
                ],
            },
            {
                'field_id': 1110355,
                'values': [
                    {'value': body.description},
                ],
            },
            {
                'field_id': 1447011,
                'values': [
                    {'value': body.size},
                ],
            },
            {
                'field_id': 1110353,
                'values': [
                    {'value': item.article},
                ],
            },
            {
                'field_id': 1450239,
                'values': [
                    {'value': str(body.lead_id)},
                ],
            },
            {
                'field_id': 1110361,
                'values': [
                    {'value': item.this_is_set},
                ],
            },
            {
                'field_id': 1110365,
                'values': [
                    {'value': body.uom},
                ],
            },
            {
                'field_id': 1450249,
                'values': [
                    {'value': f'https://ceh.amocrm.ru/catalogs/12367/detail/{bt_item_id}'},
                ],
            },
            {
                'field_id': 1450213,
                'values': [
                    {
                        'value': {
                            'entity_id': bt_item_id,
                            'entity_type': 'catalog_elements',
                            'catalog_id': 12367,
                        },
                    },
                ],
            }
        ]
        return cls(
            name=body.name,
            description=body.description,
            custom_fields_values=custom_fields,
        )

    def get_description(self):
        result = ''
        for field in self.custom_fields_values:
            if int(field['field_id']) == 1110355:
                try:
                    result = field['values'][0]['values'][0]['value']
                except KeyError:
                    result = field['values'][0]['value']
        return result

    def get_price(self):
        result = None
        for field in self.custom_fields_values:
            if int(field['field_id']) == 1110357:
                try:
                    result = int(field['values'][0]['values'][0]['value'])
                except KeyError:
                    result = int(field['values'][0]['value'])
        return result

    def get_count(self):
        result = None
        for field in self.custom_fields_values:
            if int(field['field_id']) == 1450277:
                try:
                    result = int(field['values'][0]['values'][0]['value'])
                except KeyError:
                    result = int(field['values'][0]['value'])
        return result

    def get_agent_price(self):
        result = None
        for field in self.custom_fields_values:
            if int(field['field_id']) == 1450223:
                try:
                    result = int(field['values'][0]['values'][0]['value'])
                except KeyError:
                    result = int(field['values'][0]['value'])
        return result

    def get_sizes(self):
        result = ''
        for field in self.custom_fields_values:
            if int(field['field_id']) == 1447011:
                try:
                    result = field['values'][0]['values'][0]['value']
                except KeyError:
                    result = field['values'][0]['value']
        return result

    def get_note(self):
        result = ''
        for field in self.custom_fields_values:
            if int(field['field_id']) == 1450287:
                try:
                    result = field['values'][0]['values'][0]['value']
                except KeyError:
                    result = field['values'][0]['value']
        return result

    def get_count_for_invoice(self):
        result = 0
        for field in self.custom_fields_values:
            if int(field['field_id']) == 1450285:
                try:
                    result = int(field['values'][0]['values'][0]['value'])
                except KeyError:
                    result = int(field['values'][0]['value'])
        return result

    def get_photo(self):
        result = None
        for field in self.custom_fields_values:
            if int(field['field_id']) == 1450227:
                try:
                    result = field['values'][0]['values'][0]['value']
                except KeyError:
                    result = field['values'][0]['value']
        return result

    def get_notion_parent_uid(self) -> list:
        result = []
        for field in self.custom_fields_values:
            if int(field['field_id']) == 1450221:
                try:
                    result.append(field['values'][0]['values'][0]['value'])
                except KeyError:
                    result.append(field['values'][0]['value'])
        return result


class AMOProduct(BaseModel):
    id: str = ''
    description: str = ''  # описание
    name: str = ''  # название
    custom_fields_values: list[dict]

    @model_validator(mode='before')
    def extract_fields(self: dict, *args, **kwargs) -> dict:
        for field in self.get('custom_fields_values', []):
            if field['field_id'] == 1450155:
                self['description'] = field['values'][0]['value']
        self['id'] = str(self.get('id', ''))
        return self

    def to_notion_item(self) -> Item:
        def get_custom_field_value(field_id):
            for field in self.custom_fields_values:
                if field['field_id'] == field_id:
                    return field['values'][0]['value']
            return ''

        # Преобразование Unix timestamp в ISO 8601 формат
        def convert_timestamp_to_iso8601(timestamp):
            if not timestamp:
                return ''
            dt = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
            return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        this_is_set = get_custom_field_value(1450193)
        if this_is_set == '':
            this_is_set = False
        main_price = 0
        try:
            main_price = int(get_custom_field_value(1450149))
        except ValueError:
            pass
        return Item(
            amo_id=self.id,
            id=get_custom_field_value(1450175),  # notion ID
            nid=get_custom_field_value(1450173),  # NID
            title=self.name,  # Название
            this_is_set=this_is_set,  # This is set
            article=get_custom_field_value(1450147),  # Артикул
            variants=get_custom_field_value(1450153),  # Вариации
            tags=get_custom_field_value(1450183),  # Теги
            sizes=get_custom_field_value(1450169),  # Размеры
            photo=get_custom_field_value(1450159),  # Фото
            photo_all=get_custom_field_value(1450181),  # Фото все
            description=self.description,  # Описание
            main_price=main_price,  # Цена (основная)
            price_status=get_custom_field_value(1450167),  # Статус цены
            sections=get_custom_field_value(1450185),  # Разделы
            subsections=get_custom_field_value(1450187),  # Подразделы
            catalog_status=ItemStatus(get_custom_field_value(1450165)),  # Статус каталога
            admin_link=get_custom_field_value(1450161),  # Админ-ссылка
            client_link=get_custom_field_value(1450163),  # Клиент-ссылка
            serial_no=int(get_custom_field_value(1450195)),  # Порядковый ID
            created=convert_timestamp_to_iso8601(get_custom_field_value(1450179)),  # Created time
            last_edited_time=convert_timestamp_to_iso8601(get_custom_field_value(1450177)),  # Last edited time
            last_edited_by=get_custom_field_value(1450189),  # Last edited by
            created_by=get_custom_field_value(1450191),  # Created by
            price_formula=get_custom_field_value(1450151),  # price formula
            clear_title=get_custom_field_value(1450205),
        )

    @classmethod
    def from_notion_item(cls, item: Item) -> AMOProduct:
        dt = datetime.strptime(
            item.created,
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ).replace(
            tzinfo=timezone.utc,
        ).astimezone()
        created = (dt.strftime('%Y-%m-%dT%H:%M:%S%z')[:-2] + ':'
                   + dt.strftime('%Y-%m-%dT%H:%M:%S%z')[-2:])
        dt = datetime.strptime(
            item.last_edited_time,
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ).replace(
            tzinfo=timezone.utc,
        ).astimezone()
        last_edited_time = (dt.strftime('%Y-%m-%dT%H:%M:%S%z')[:-2] + ':'
                   + dt.strftime('%Y-%m-%dT%H:%M:%S%z')[-2:])

        custom_fields = [
            {
                'field_id': 1450193,
                'values': [
                    {'value': item.this_is_set},
                ],
            },
            {
                'field_id': 1450169,
                'values': [
                    {'value': item.sizes},
                ],
            },
            {
                'field_id': 1450155,
                'values': [
                    {'value': item.description},
                ],
            },
            {
                'field_id': 1450153,
                'values': [
                    {'value': item.variants},
                ],
            },
            {
                'field_id': 1450183,
                'values': [
                    {'value': item.tags},
                ],
            },
            {
                'field_id': 1450159,
                'values': [
                    {'value': item.photo},
                ],
            },
            {
                'field_id': 1450181,
                'values': [
                    {'value': item.photo_all},
                ],
            },
            {
                'field_id': 1450149,
                'values': [
                    {'value': item.main_price},
                ],
            },
            {
                'field_id': 1450167,
                'values': [
                    {'value': item.price_status},
                ],
            },
            {
                'field_id': 1450147,
                'values': [
                    {'value': item.article},
                ],
            },
            {
                'field_id': 1450185,
                'values': [
                    {'value': item.sections},
                ],
            },
            {
                'field_id': 1450187,
                'values': [
                    {'value': item.subsections},
                ],
            },
            {
                'field_id': 1450165,
                'values': [
                    {'value': item.catalog_status},
                ],
            },
            {
                'field_id': 1450161,
                'values': [
                    {'value': item.admin_link},
                ],
            },
            {
                'field_id': 1450163,
                'values': [
                    {'value': item.client_link},
                ],
            },
            {
                'field_id': 1450195,
                'values': [
                    {'value': item.serial_no},
                ],
            },
            {
                'field_id': 1450179,
                'values': [
                    {'value': created},
                ],
            },
            {
                'field_id': 1450177,
                'values': [
                    {'value': last_edited_time},
                ],
            },
            {
                'field_id': 1450189,
                'values': [
                    {'value': item.last_edited_by},
                ],
            },
            {
                'field_id': 1450191,
                'values': [
                    {'value': item.created_by},
                ],
            },
            {
                'field_id': 1450173,
                'values': [
                    {'value': item.nid},
                ],
            },
            {
                'field_id': 1450175,
                'values': [
                    {'value': item.id},
                ],
            },
            {
                'field_id': 1450151,
                'values': [
                    {'value': item.price_formula},
                ],
            },
            {
                'field_id': 1450205,
                'values': [
                    {'value': item.clear_title},
                ],
            }
        ]
        return cls(
            id=item.amo_id,
            description=item.description,
            name=item.title,
            custom_fields_values=custom_fields,
        )


def transform_custom_fields_values(fields: dict):
    transformed = []
    for field_index, field_data in fields.items():
        field_id = field_data['id']
        field_data.pop('id')
        transformed.append({
            'field_id': field_id,
            'values': [field_data],
        })
    return transformed


def parse_dt_product_update(data) -> tuple[list[AMODTProduct], list[AMODTProduct], list[int]]:
    data = {k: v[0] if len(v) == 1 else v for k, v in data.items()}
    data = build_nested_dict(data)

    add_dts, update_dts, delete_dts = [], [], []

    catalogs = data.get('catalogs', {})
    add_items = catalogs.get('add', {})
    update_items = catalogs.get('update', {})
    delete_items = catalogs.get('delete', {})

    for item in add_items.values():
        item['custom_fields_values'] = transform_custom_fields_values(item['custom_fields'])
        item = AMODTProduct(**item)
        add_dts.append(item)

    for item in update_items.values():
        item['custom_fields_values'] = transform_custom_fields_values(item['custom_fields'])
        item = AMODTProduct(**item)
        update_dts.append(item)

    for item in delete_items.items():
        delete_dts.append(int(item[1]['id']))

    return add_dts, update_dts, delete_dts
