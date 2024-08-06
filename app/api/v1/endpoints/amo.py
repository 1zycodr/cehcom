from typing import Any

from fastapi import APIRouter, Body, BackgroundTasks

from app.services import NotionService

router = APIRouter()


@router.post(
    '/docs',
    description='Хук для google docs',
)
def docs(
        payload: Any = Body(None),
):
    print(payload)


@router.get(
    '/sync-catalog',
    description='Принудительная синхронизация всего каталога с amoCRM',
)
def sync_catalog(background_tasks: BackgroundTasks):
    background_tasks.add_task(NotionService.sync_with_amo, True)
    return 'Процесс обновления запущен'


@router.get(
    '/sync-catalog-updated',
    description='Принудительная синхронизация обновлённых записей каталога с amoCRM',
)
def sync_catalog_updated(background_tasks: BackgroundTasks):
    background_tasks.add_task(NotionService.sync_with_amo)
    return 'Процесс обновления запущен'
