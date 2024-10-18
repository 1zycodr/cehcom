from __future__ import annotations
from enum import Enum

from pydantic import BaseModel

from app.repository.tgbot import Alert
from app.utils.file_storage import save_file_from_url


class ItemStatus(str, Enum):
    delete = 'Удалить'
    off = 'Отключено'
    reserve = 'Резерв'
    on = 'Включено'
    on_usn = 'Включено только в УСН'
    individual = 'Индивидуальный'


class ItemWPProductType(str, Enum):
    simple = 'Простой товар'
    variable = 'Вариация'
    main = 'Главный товар'


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
    subproducts_ids: list[str] | None = None
    main_item: str = ''
    wp_description: str = ''
    description_variations: str = ''
    wp_product_type: ItemWPProductType = ''

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
        if result['photo'] != '':
            try:
                result['photo'] = save_file_from_url(result['photo'], f"{result['nid']}.jpg")
            except Exception as e:
                Alert.critical(f'Ошибка загрузки фото с Notion: {e}')
                result['photo'] = ''
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
        result['wp_description'] = cls.getter(props, 'WP: Описание', 'formula', 'string')
        result['wp_product_type'] = cls.getter(props, 'WP: Тип продукта', 'formula', 'string')
        try:
            result['description_variations'] = props['Описание вариации']['rich_text'][0]['text']['content']
        except (KeyError, IndexError):
            result['description_variations'] = ''
        # подпродукты и главный продукт собираем как связанные
        linked_products = []
        subproducts_ids = []
        subproducts = cls.getter(props, 'Подпродукт', 'relation')
        for relation in subproducts:
            linked_products.append(relation['id'])
            subproducts_ids.append(relation['id'])
        main_products = cls.getter(props, 'Главный продукт', 'relation')
        for relation in main_products:
            linked_products.append(relation['id'])
            result['main_item'] = relation['id']
        result['linked_ids'] = linked_products
        result['subproducts_ids'] = subproducts_ids
        return cls(**result)

    @staticmethod
    def getter(values: dict, *fields: str) -> str | int | bool | list[dict] | None:
        for field in fields:
            values = values.get(field, {})
            if values == {} or values is None:
                return ''
        return values


class WPItemType(str, Enum):
    simple = 'simple'
    variable = 'variable'


class WPItemStatus(str, Enum):
    draft = 'draft'
    publish = 'publish'


class WPItem(BaseModel):
    wp_id: int | None = None
    title: str = ''
    type: WPItemType = ''
    short_description: str = ''
    price: int = 0
    sku: str = ''
    nid: str = ''
    variation_description: str = ''
    status: WPItemStatus = ''
    images: list[str]
    manage_stock: bool = True
    stock_status: str = 'onbackorder'

    @classmethod
    def from_notion_item(cls, item: Item) -> WPItem:
        data = {
            'nid': item.nid,
            'title': item.clear_title,
            'short_description': item.wp_description,
            'price': item.main_price,
            'sku': item.article,
            'variation_description': item.description_variations,
            'images': item.photo_all.split(';\n\n'),
        }
        if item.catalog_status in (ItemStatus.on, ItemStatus.on_usn):
            data['status'] = WPItemStatus.publish
        else:
            data['status'] = WPItemStatus.draft
        if item.wp_product_type == ItemWPProductType.simple:
            data['type'] = WPItemType.simple
        else:
            data['type'] = WPItemType.variable
        return cls(**data)

    @classmethod
    def from_response(cls, resp: dict) -> WPItem:
        attributes = resp.get('attributes', [])
        attributes = {
            attr['id']: attr['options']
            for attr in attributes
        }
        data = {
            'wp_id': resp.get('id', None),
            'title': resp.get('name', ''),
            'type': resp.get('type', ''),
            'description': resp.get('description', ''),
            'price': int(float(resp.get('price', 0))),
            'sku': resp.get('sku', ''),
            'nid': attributes.get(9, [''])[0],
        }
        return cls(**data)

    @classmethod
    def to_dict(cls, item: WPItem) -> dict:
        result = {
            'name': item.title,
            'type': item.type,
            'regular_price': item.price,
            'description': item.description,
            'short_description': item.description,
            'images': [
                {
                    'src': item.photo,
                }
            ],
            'attributes': [
                {
                    'id': 9,
                    'options': [item.nid],
                },
            ],
        }
        return result
