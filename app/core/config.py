from __future__ import annotations

import os
import redis
from redis.client import Redis

from enum import Enum

from pydantic_settings import BaseSettings
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class Settings(BaseSettings):

    class Environment(str, Enum):
        local = 'local'
        dev = 'dev'
        prod = 'prod'

    PROJECT_NAME: str = 'Cehcom API'

    # URI settings
    ROOT_URL: str = f'/api'
    API_V1_STR: str = f'{ROOT_URL}/v1'
    DOCS_URL: str = f'{ROOT_URL}-docs/docs'
    OPENAPI_JSON_URL: str = f'{ROOT_URL}-docs/openapi.json'

    # Environment settings
    ENVIRONMENT: Environment = Environment.dev  # local, dev, prod
    COUNTRY_ISO: str = 'RU'

    # AMOCRM credentials
    AMOCRM_SUBDOMAIN: str
    AMOCRM_CLIENT_ID: str
    AMOCRM_CLIENT_SECRET: str
    AMOCRM_REDIRECT_URL: str
    AMOCRM_ACCESS_TOKEN: str = ''
    AMOCRM_REFRESH_TOKEN: str = ''

    # Notion secrets
    NOTION_SECRET: str

    # Telegram
    TG_TOKEN: str

    # Redis
    REDIS_HOST: str = 'redis'


settings = Settings()
red: Redis = redis.Redis(host=settings.REDIS_HOST, port=6379, db=0)
