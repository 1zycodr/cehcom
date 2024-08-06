import time

import requests

from itertools import islice
from time import sleep

from app.core import settings
from app.schemas import Item, AMOProduct


class AmoRepo:

    @classmethod
    def get_product_by_nid(cls, nid: str) -> Item | None:
        time.sleep(.2)
        url = '/api/v4/catalogs/9035/elements'
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
        params = {
            'query': nid,
        }

        response = requests.get(
            "https://{}.amocrm.ru{}".format(settings.AMOCRM_SUBDOMAIN, url),
            headers=headers,
            params=params,
        )

        if response.status_code == 204:
            return None

        # TODO добавить считывание пагинации
        elements = response.json().get('_embedded', {}).get('elements', [])
        for elem in elements:
            item = AMOProduct(**elem).to_notion_item()
            if item.nid == nid:
                return item

        return None

    @classmethod
    def chunks(cls, iterable, size):
        iterator = iter(iterable)
        for first in iterator:
            yield [first] + list(islice(iterator, size - 1))

    @classmethod
    def add_products(cls, items: list[Item]):
        if len(items) == 0:
            return
        url = '/api/v4/catalogs/9035/elements'
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
        products = [
            AMOProduct.from_notion_item(item).dict() for item in items
        ]
        for p in products:
            p.pop('id', None)
        for i, batch in enumerate(cls.chunks(products, 50)):
            n = 1
            while n != 6:
                sleep(0.2)
                response = requests.post(
                    "https://{}.amocrm.ru{}".format(settings.AMOCRM_SUBDOMAIN, url),
                    headers=headers,
                    json=batch,
                )

                if response.status_code == 200:
                    print(f"Batch {i + 1} added successfully!")
                    break
                else:
                    sleep(1)
                    print(f"Failed to add batch {i + 1}. Retrying...", n)
                    n += 1

    @classmethod
    def patch_items(cls, items: list[Item]):
        if len(items) == 0:
            return
        url = f'/api/v4/catalogs/9035/elements'
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
        data = [
            {
                "id": int(item.amo_id),
                "name": item.title,
                "custom_fields_values": AMOProduct.from_notion_item(item).custom_fields_values,
            }
            for item in items
        ]
        response = requests.patch(
            "https://{}.amocrm.ru{}".format(settings.AMOCRM_SUBDOMAIN, url),
            headers=headers,
            json=data
        )
        if response.status_code != 200:
            print('Failed to delete elements from AMO:', response.text)

    @classmethod
    def get_all_products(cls) -> list[Item]:
        time.sleep(.2)
        url = '/api/v4/catalogs/9035/elements'
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        page = 1
        items = []

        while True:
            params = {
                'page': page,
                'limit': 250,
            }

            response = requests.get(
                "https://{}.amocrm.ru{}".format(settings.AMOCRM_SUBDOMAIN, url),
                headers=headers,
                params=params,
            )

            if response.status_code != 200:
                print(f"Failed to fetch products: {response.status_code} - {response.text}")
                break

            elements = response.json().get('_embedded', {}).get('elements', [])
            if not elements:
                break

            for elem in elements:
                item = AMOProduct(**elem).to_notion_item()
                items.append(item)

            print(f'Loaded products from amo: {len(items)}')

            page += 1
            time.sleep(0.2)
        return items
