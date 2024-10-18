from __future__ import annotations

import redis

from redis.client import Redis

from enum import Enum
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings
from pydantic_core.core_schema import FieldValidationInfo
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

    # Wordpress credentials
    WP_USERNAME: str
    WP_PASSWORD: str

    # Notion secrets
    NOTION_SECRET: str

    # Telegram
    TG_TOKEN: str

    # Redis
    REDIS_HOST: str = 'redis'

    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_DB: str = 'postgres'
    POSTGRES_PORT: int
    POSTGRES_ECHO: bool
    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None

    # files
    UPLOAD_DIR: str = 'media'

    # default photo link
    DEFAULT_PHOTO: str = 'https://api.cehcom.kz/media/default.jpg'

    @field_validator('SQLALCHEMY_DATABASE_URI', mode='after')
    def assemble_db_connection(cls, v: str, values: FieldValidationInfo) -> str:
        if v is not None:
            if isinstance(v, str):
                return v
        return str(PostgresDsn.build(
            scheme="postgresql",
            port=values.data.get("POSTGRES_PORT"),
            username=values.data.get("POSTGRES_USER"),
            password=values.data.get("POSTGRES_PASSWORD"),
            host=values.data.get("POSTGRES_SERVER"),
            path=f"{values.data.get('POSTGRES_DB') or ''}",
        ))


settings = Settings()
red: Redis = redis.Redis(host=settings.REDIS_HOST, port=6379, db=0)
