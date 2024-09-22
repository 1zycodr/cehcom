import time

import requests

from itertools import islice
from time import sleep

from app.core import settings
from app.schemas import Item, AMOProduct, AMODTProduct
from app.schemas.lead import LeadUpdate


class AmoRepo:

    @classmethod
    def get_product_by_nid(cls, nid: str) -> Item | None:
        time.sleep(.2)
        url = '/api/v4/catalogs/12367/elements'
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
        url = '/api/v4/catalogs/12367/elements'
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

    @staticmethod
    def chunk_list(data, chunk_size):
        """Функция для разбиения списка на чанки по определённому размеру."""
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    @classmethod
    def patch_items(cls, items: list[Item]):
        if len(items) == 0:
            return
        url = f'/api/v4/catalogs/12367/elements'
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
        for i, batch in enumerate(cls.chunk_list(data, 50)):
            response = requests.patch(
                "https://{}.amocrm.ru{}".format(settings.AMOCRM_SUBDOMAIN, url),
                headers=headers,
                json=batch
            )
            if response.status_code != 200:
                print(f"Failed to update amo batch: {response.status_code} - {response.text}")
            else:
                print(f"Batch {i} updated successfully")

    @classmethod
    def get_all_products(cls) -> list[Item]:
        time.sleep(.2)
        url = '/api/v4/catalogs/12367/elements'
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

    @classmethod
    def attach_item_to_lead(cls, lead_id: int, item_id: int, quantity: int = None):
        time.sleep(.2)
        url = f'/api/v4/leads/{lead_id}/link'
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
        data = [
            {
                "to_entity_id": item_id,
                "to_entity_type": "catalog_elements",
                "metadata": {
                    "catalog_id": 9035,
                }
            }
        ]
        if quantity is not None:
            data[0]['metadata']['quantity'] = float(quantity)
        response = requests.post(
            "https://{}.amocrm.ru{}".format(settings.AMOCRM_SUBDOMAIN, url),
            headers=headers,
            json=data,
        )
        if response.status_code == 200:
            print("Item attached to lead successfully!", lead_id, item_id)
        else:
            print("Failed to attach item to lead", lead_id, item_id)

    @classmethod
    def get_lead_items_ids(cls, lead_id: int) -> (list[(int, int)], str, str):
        time.sleep(.2)
        url = f'/api/v4/leads/{lead_id}'
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
        params = {
            'with': 'catalog_elements'
        }
        response = requests.get("https://{}.amocrm.ru{}".format(
            settings.AMOCRM_SUBDOMAIN, url,
        ), headers=headers, params=params)
        items = list()
        lead_id = ''
        lead_uid = ''
        if response.status_code == 200:
            data = response.json()
            elems = data.get('_embedded', {}).get('catalog_elements', [])
            for elem in elems:
                items.append((elem['id'], elem['metadata']['quantity']))
            for field in data['custom_fields_values']:
                if field['field_id'] == 1450275:
                    lead_id = field['values'][0]['value'][3:]
                if field['field_id'] == 1450043:
                    lead_uid = field['values'][0]['value']
        else:
            print(f"Failed to get lead items", response.status_code, response.text)
        return items, lead_id, lead_uid

    @classmethod
    def add_dt_product(cls, item: AMODTProduct) -> AMODTProduct | None:
        time.sleep(.2)
        url = '/api/v4/catalogs/9035/elements'
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
        n = 1
        while n != 6:
            sleep(0.2)
            response = requests.post(
                "https://{}.amocrm.ru{}".format(settings.AMOCRM_SUBDOMAIN, url),
                headers=headers,
                json=[item.model_dump()],
            )
            if response.status_code == 200:
                item.id = response.json()['_embedded']['elements'][0]['id']
                print(f"Item created successfully!")
                return item
            else:
                sleep(1)
                print(f"Failed to create item", n)
                n += 1

    @classmethod
    def update_lead_fields(cls, lead_id: int, fields: dict):
        time.sleep(.2)
        url = f'/api/v4/leads/{lead_id}'
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        response = requests.patch(
            "https://{}.amocrm.ru{}".format(settings.AMOCRM_SUBDOMAIN, url),
            headers=headers,
            json=fields,
        )
        if response.status_code == 200:
            print(f"Lead {lead_id} updated successfully!")
        else:
            print(f"Failed to update lead {lead_id}: {response.status_code} - {response.text}")

    @classmethod
    def update_leads(cls, leads: list[LeadUpdate]):
        if len(leads) == 0:
            return
        time.sleep(.2)
        url = f'/api/v4/leads'
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
        data = [
            lead.dict()
            for lead in leads
        ]
        for i, batch in enumerate(cls.chunk_list(data, 50)):
            response = requests.patch(
                "https://{}.amocrm.ru{}".format(settings.AMOCRM_SUBDOMAIN, url),
                headers=headers,
                json=batch,
            )
            if response.status_code != 200:
                print(f"Failed to update amo batch: {response.status_code} - {response.text}")
            else:
                print(f"Batch {i} updated successfully")

    @classmethod
    def update_lead_item_after_creation(cls, item_id, fields: dict):
        time.sleep(.2)
        url = f'/api/v4/catalogs/9035/elements/{item_id}'
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
        response = requests.patch(
            "https://{}.amocrm.ru{}".format(settings.AMOCRM_SUBDOMAIN, url),
            headers=headers,
            json=fields,
        )
        if response.status_code == 200:
            print(f"Item {item_id} updated successfully!")
        else:
            print(f"Failed to update item {item_id}: {response.status_code} - {response.text}")

    @classmethod
    def get_lead_products(cls, ids: list[int]) -> list[AMODTProduct]:
        time.sleep(.2)
        url = '/api/v4/catalogs/9035/elements'
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        result = []

        for id in ids:
            params = {
                'id': id,
            }

            response = requests.get(
                "https://{}.amocrm.ru{}".format(settings.AMOCRM_SUBDOMAIN, url),
                headers=headers,
                params=params,
            )
            if response.status_code == 204:
                continue
            data = response.json()
            element = data.get('_embedded', {}).get('elements', [None])[0]
            if element is not None:
                result.append(AMODTProduct(**element))

        return result

