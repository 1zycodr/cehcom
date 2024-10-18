import requests

from requests.auth import HTTPBasicAuth

from app.core import settings
from app.schemas import WPItem


class WordpressRepository:
    url = 'https://dev.cehcom.kz/wp-json/wc'

    @classmethod
    def add_product(cls, data: dict):
        url = f'{cls.url}/v3/products'
        response = requests.post(
            url,
            json=data,
            auth=HTTPBasicAuth(settings.WP_USERNAME, settings.WP_PASSWORD)
        )
        if response.status_code != 201:
            print(f"Add item failed: {response.status_code} - {response.text}")
        return response.json()

    @classmethod
    def get_all_products(cls):
        url = f'{cls.url}/v3/products'
        params = {
            'per_page': 1,
        }
        response = requests.get(
            url,
            auth=HTTPBasicAuth(settings.WP_USERNAME, settings.WP_PASSWORD),
            params=params,
        )
        if response.status_code != 200:
            print(f"WP get items failed: {response.status_code} - {response.text}")
        response = response.json()
        result = [
            WPItem.from_response(item)
            for item in response
        ]
        return result
