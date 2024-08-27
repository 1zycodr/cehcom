from __future__ import annotations
from datetime import datetime, timezone

from pydantic import BaseModel, model_validator

from .api import LeadAddItemRequest
from .notion import Item, ItemStatus


class AMODTProduct(BaseModel):
    id: int = 0
    name: str = ''
    description: str = ''
    custom_fields_values: list[dict]

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
                    {'value': item.description},
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
