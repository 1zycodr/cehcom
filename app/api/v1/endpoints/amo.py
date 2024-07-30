from typing import Any

from fastapi import APIRouter, Body

from errors.response import Respond

from app.schemas import *
from app.services.amocrm import AMOCRMService

router = APIRouter()


@router.post(
    '/init-oauth2',
    description='Обновление авторизационных токенов',
)
def init_oauth2(
        body: InitOauth2Request,
) -> Respond[str]:
    try:
        AMOCRMService.init_oauth2(body.code)
    except Exception as ex:
        return Respond(str(ex))


@router.post(
    '/docs',
    description='Хук для google docs',
)
def docs(
        payload: Any = Body(None),
):
    print(payload)
