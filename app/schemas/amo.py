from pydantic import BaseModel, Field


class InitOauth2Request(BaseModel):
    code: str = Field(description='Авторизационный код с интеграции')
