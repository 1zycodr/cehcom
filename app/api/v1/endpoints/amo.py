from typing import Any

from fastapi import APIRouter, Body, BackgroundTasks, Request

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
async def process_data(request: Request):
    # Получение тела запроса в виде байтов
    body_bytes = await request.body()

    # Преобразование байтов в строку для печати
    body_str = body_bytes.decode('utf-8')

    # Печать тела запроса
    print("Request body:", body_str)

    # Вы также можете получить тело запроса как JSON
    json_payload = await request.json()

    return {"received_data": json_payload}
