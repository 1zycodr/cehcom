from typing import Any

from fastapi import APIRouter, Body, BackgroundTasks

from app.core.config import red
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
    '/sync-catalog-full',
    description='Принудительная синхронизация всего каталога с amoCRM',
)
def sync_catalog(background_tasks: BackgroundTasks):
    if red.get('sync-running') is not None:
        return 'Запрос проигнорирован. Процесс полного обновления уже был запущен недавно.'
    red.set('sync-running', '1')
    background_tasks.add_task(NotionService.sync_with_amo, True)
    return 'Процесс полного обновления запущен.'


@router.get(
    '/sync-catalog-edited',
    description='Принудительная синхронизация обновлённых записей каталога с amoCRM',
)
def sync_catalog_updated(background_tasks: BackgroundTasks):
    if red.get('sync-running') is not None:
        return 'Запрос проигнорирован. Процесс обновления уже был запущен недавно.'
    red.set('sync-running', '1')
    background_tasks.add_task(NotionService.sync_with_amo)
    return 'Процесс обновления запущен.'


@router.post(
    '/lead-update',
    description='Хук для обновления сделок в amoCRM',
)
def lead_update(
        payload: Any = Body(None),
):
    print(payload)
    return 'ok'
