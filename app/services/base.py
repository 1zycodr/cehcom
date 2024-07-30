import json
import requests

from logging import Logger
from typing import Literal, Any
from urllib.parse import urljoin
from requests import HTTPError

from errors import ExternalIntegrationError


class BaseHTTPService:

    def __init__(self, base_url: str, logger: Logger):
        self.__url = base_url
        self.__logger = logger

    def _fetch(
            self,
            path: str,
            method: Literal['GET', 'POST', 'PUT'],
            params: dict[str, Any] | list[dict[str, Any]] | None = None,
            headers: dict[str, str] | None = None,
            body: dict[str, Any] | list[Any] = None,
            auth: tuple[str, str] = None,
            jwt: str | None = None,
            timeout: int = 30,
    ):
        # готовим данные для запроса
        if jwt is not None:
            headers = headers or {}
            headers['Authorization'] = f'Bearer {jwt}'

        url = urljoin(self.__url, path)

        request_params = {
            'url': url,
            'method': method,
            'headers': headers,
            'params': params,
            'auth': auth,
            'timeout': timeout,
        }
        if body:
            request_params['json'] = body

        # запрос
        response = requests.request(**request_params)

        # парсим, логируем запрос
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            response_json = None

        response_text = response.text
        response_data = response_json if response_json else response_text
        self.__logger.warning({
            'type': '_fetch',
            'request': request_params,
            'response': response_data,
        })

        # кидаем исключение если запрос провалился
        try:
            response.raise_for_status()
        except HTTPError as ex:
            raise ExternalIntegrationError(
                f'Bad request: {str(ex)}',
                request_params,
                response_data,
            ) from ex

        return response_data
