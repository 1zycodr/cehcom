import requests

from app.core import settings
from app.services.base import BaseHTTPService


class AMOCRMService(BaseHTTPService):

    @classmethod
    def init_oauth2(cls, code: str):
        data = {
            "client_id": settings.AMOCRM_CLIENT_ID,
            "client_secret": settings.AMOCRM_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.AMOCRM_REDIRECT_URL,
        }

        response = requests.post(
            "https://{}.amocrm.ru/oauth2/access_token".format(settings.AMOCRM_SUBDOMAIN),
            json=data,
        )

        if response.status_code != 200:
            raise Exception(response.text)

        result = response.json()

        access_token, refresh_token = result["access_token"], result["refresh_token"]
        settings.save_amocrm_tokens(access_token, refresh_token)

    @classmethod
    def test(cls):
        url = '/api/v4/leads/' + str(29053651)
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {"Authorization": access_token}
        response = requests.get("https://{}.amocrm.ru{}".format(
            settings.AMOCRM_SUBDOMAIN, url), headers=headers).json()
        print(response)

    @classmethod
    def list_catalogs(cls):
        url = '/api/v4/catalogs/9035/elements'
        access_token = "Bearer " + settings.AMOCRM_ACCESS_TOKEN
        headers = {"Authorization": access_token}
        response = requests.get(
            "https://{}.amocrm.ru{}".format(settings.AMOCRM_SUBDOMAIN, url),
            headers=headers,
            # params={'id': 9035}
        )
        print(response)

