from __future__ import annotations
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


settings = Settings()
