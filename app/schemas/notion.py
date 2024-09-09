from __future__ import annotations
from enum import Enum

from pydantic import BaseModel


class ItemStatus(str, Enum):
    delete = 'Удалить'
    off = 'Отключено'
    reserve = 'Резерв'
    on = 'Включено'
    on_usn = 'Включено только в УСН'


class Item(BaseModel):
    amo_id: str = ''  # ID
    id: str = ''  # notion_id
    nid: str = ''  # NID
    title: str = ''  # Название формула
    clear_title: str = ''  # Название формула без артикула
    this_is_set: bool = False  # This is set
    article: str = ''  # Артикул
    variants: str = ''  # Вариации
    tags: str = ''  # Теги формула
    sizes: str = ''  # Размеры формула
    photo: str = ''  # Фото формула
    photo_all: str = ''  # Фото все формула
    description: str = ''  # Описание формула
    main_price: int = 0  # Цена (основная)
    price_formula: str = ''  # Цена (формула)
    price_status: str = ''  # Статус цены
    sections: str = ''  # Разделы формула
    subsections: str = ''  # Подразделы формула
    catalog_status: ItemStatus = ''  # Статус каталога
    admin_link: str = ''  # Админ-ссылка
    client_link: str = ''  # Клиент-ссылка
    serial_no: int = ''  # Порядковый ID
    created: str = ''  # Created time
    last_edited_time: str = ''  # Last edited time
    last_edited_by: str = ''  # last edited by
    created_by: str = ''  # Created by
    linked_ids: list[str] | None = None

    @classmethod
    def from_response(cls, resp: dict) -> Item:
        props = resp['properties']
        result = dict()
        result['id'] = cls.getter(resp, 'id')
        result['nid'] = cls.getter(props, 'NID', 'formula', 'string')
        result['title'] = cls.getter(props, 'Название формула', 'formula', 'string')
        result['clear_title'] = cls.getter(props, 'Название без артикула формула', 'formula', 'string')
        result['this_is_set'] = cls.getter(props, 'This is set', 'formula', 'boolean')
        result['article'] = cls.getter(props, 'Артикул', 'formula', 'string')
        result['variants'] = cls.getter(props, 'Вариации', 'formula', 'string')
        result['tags'] = cls.getter(props, 'Теги формула', 'formula', 'string')
        result['sizes'] = cls.getter(props, 'Размеры формула', 'formula', 'string')
        result['photo'] = cls.getter(props, 'Фото формула', 'formula', 'string')
        result['photo_all'] = cls.getter(props, 'Фото все формула', 'formula', 'string')
        result['description'] = cls.getter(props, 'Описание формула', 'formula', 'string')
        main_price = cls.getter(props, 'Цена (основная)', 'number')
        if type(main_price) is not int:
            main_price = 0
        result['main_price'] = main_price
        result['price_formula'] = cls.getter(props, 'Цена 2-формула', 'formula', 'string')
        result['price_status'] = cls.getter(props, 'Статус цены', 'status', 'name')
        result['sections'] = cls.getter(props, 'Разделы формула', 'formula', 'string')
        result['subsections'] = cls.getter(props, 'Подразделы формула', 'formula', 'string')
        result['catalog_status'] = cls.getter(props, 'Каталог статус', 'status', 'name')
        result['admin_link'] = cls.getter(props, 'Админ-ссылка', 'formula', 'string')
        result['client_link'] = cls.getter(props, 'Клиент-ссылка', 'formula', 'string')
        result['serial_no'] = cls.getter(props, 'Порядковый ID', 'unique_id', 'number')
        result['created'] = cls.getter(resp, 'created_time')
        result['last_edited_time'] = cls.getter(resp, 'last_edited_time')
        result['last_edited_by'] = cls.getter(resp, 'last_edited_by', 'id')
        result['created_by'] = cls.getter(resp, 'created_by', 'id')

        # подпродукты и главный продукт собираем как связанные
        linked_products = []
        subproducts = cls.getter(props, 'Подпродукт', 'relation')
        for relation in subproducts:
            linked_products.append(relation['id'])
        main_products = cls.getter(props, 'Главный продукт', 'relation')
        for relation in main_products:
            linked_products.append(relation['id'])
        result['linked_ids'] = linked_products
        return cls(**result)

    @staticmethod
    def getter(values: dict, *fields: str):
        for field in fields:
            values = values.get(field, {})
            if values == {} or values is None:
                return ''
        return values
