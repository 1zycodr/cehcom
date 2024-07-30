from fastapi import APIRouter

from app.api.v1 import endpoints as v1

api_router = APIRouter()

api_router.include_router(
    v1.amo.router,
    prefix='',
    tags=['AMOCRM'],
)
