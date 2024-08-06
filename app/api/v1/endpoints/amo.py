from typing import Any

from fastapi import APIRouter, Body

from errors.response import Respond

from app.schemas import *

router = APIRouter()


@router.post(
    '/docs',
    description='Хук для google docs',
)
def docs(
        payload: Any = Body(None),
):
    print(payload)
