from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, model_validator

from .notion import Item, ItemStatus


class AMOProduct(BaseModel):
    id: str = ''
    description: str = ''  # описание
    name: str = ''  # название
    custom_fields_values: list[dict]

    @model_validator(mode='before')
    def extract_fields(self: dict, *args, **kwargs) -> dict:
        for field in self.get('custom_fields_values', []):
            if field['field_id'] == 1110355:
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

        this_is_set = get_custom_field_value(1110361)
        if this_is_set == '':
            this_is_set = False
        main_price = 0
        try:
            main_price = int(get_custom_field_value(1110357))
        except ValueError:
            pass
        return Item(
            amo_id=self.id,
            id=get_custom_field_value(1450067),  # notion ID
            nid=get_custom_field_value(1450031),  # NID
            title=self.name,  # Название
            this_is_set=this_is_set,  # This is set
            article=get_custom_field_value(1110353),  # Артикул
            variants=get_custom_field_value(1447487),  # Вариации
            tags=get_custom_field_value(1448269),  # Теги
            sizes=get_custom_field_value(1447011),  # Размеры
            photo=get_custom_field_value(1431731),  # Фото
            photo_all=get_custom_field_value(1447961),  # Фото все
            description=self.description,  # Описание
            main_price=main_price,  # Цена (основная)
            price_status=get_custom_field_value(1447005),  # Статус цены
            sections=get_custom_field_value(1448271),  # Разделы
            subsections=get_custom_field_value(1448273),  # Подразделы
            catalog_status=ItemStatus(get_custom_field_value(1447003)),  # Статус каталога
            admin_link=get_custom_field_value(1447001),  # Админ-ссылка
            client_link=get_custom_field_value(1447567),  # Клиент-ссылка
            serial_no=int(get_custom_field_value(1447015)),  # Порядковый ID
            created=convert_timestamp_to_iso8601(get_custom_field_value(1447019)),  # Created time
            last_edited_time=convert_timestamp_to_iso8601(get_custom_field_value(1447017)),  # Last edited time
            last_edited_by=get_custom_field_value(1450027),  # Last edited by
            created_by=get_custom_field_value(1450029),  # Created by
            price_formula=get_custom_field_value(1447565),  # price formula
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
                'field_id': 1110361,
                'values': [
                    {'value': item.this_is_set},
                ],
            },
            {
                'field_id': 1447011,
                'values': [
                    {'value': item.sizes},
                ],
            },
            {
                'field_id': 1110355,
                'values': [
                    {'value': item.description},
                ],
            },
            {
                'field_id': 1447487,
                'values': [
                    {'value': item.variants},
                ],
            },
            {
                'field_id': 1448269,
                'values': [
                    {'value': item.tags},
                ],
            },
            {
                'field_id': 1431731,
                'values': [
                    {'value': item.photo},
                ],
            },
            {
                'field_id': 1447961,
                'values': [
                    {'value': item.photo_all},
                ],
            },
            {
                'field_id': 1110357,
                'values': [
                    {'value': item.main_price},
                ],
            },
            {
                'field_id': 1447005,
                'values': [
                    {'value': item.price_status},
                ],
            },
            {
                'field_id': 1110353,
                'values': [
                    {'value': item.article},
                ],
            },
            {
                'field_id': 1448271,
                'values': [
                    {'value': item.sections},
                ],
            },
            {
                'field_id': 1448273,
                'values': [
                    {'value': item.subsections},
                ],
            },
            {
                'field_id': 1447003,
                'values': [
                    {'value': item.catalog_status},
                ],
            },
            {
                'field_id': 1447001,
                'values': [
                    {'value': item.admin_link},
                ],
            },
            {
                'field_id': 1447567,
                'values': [
                    {'value': item.client_link},
                ],
            },
            {
                'field_id': 1447015,
                'values': [
                    {'value': item.serial_no},
                ],
            },
            {
                'field_id': 1447019,
                'values': [
                    {'value': created},
                ],
            },
            {
                'field_id': 1447017,
                'values': [
                    {'value': last_edited_time},
                ],
            },
            {
                'field_id': 1450027,
                'values': [
                    {'value': item.last_edited_by},
                ],
            },
            {
                'field_id': 1450029,
                'values': [
                    {'value': item.created_by},
                ],
            },
            {
                'field_id': 1450031,
                'values': [
                    {'value': item.nid},
                ],
            },
            {
                'field_id': 1450067,
                'values': [
                    {'value': item.id},
                ],
            },
            {
                'field_id': 1447565,
                'values': [
                    {'value': item.price_formula},
                ],
            },
        ]
        return cls(
            id=item.amo_id,
            description=item.description,
            name=item.title,
            custom_fields_values=custom_fields,
        )
