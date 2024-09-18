import urllib

from typing import Any

from fastapi import APIRouter, Body, BackgroundTasks, Request, Depends

from app.core import get_db
from app.core.config import red
from app.core.db import SessionLocal
from app.repository.amocrm import AmoRepo
from app.repository.tgbot import Alert
from app.schemas import LeadAddItemRequest, AMODTProduct, LeadSyncItemsRequest, parse_dt_product_update
from app.schemas.lead import parse_lead_update
from app.services import NotionService, AMOService

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
    '/sync-leads-full',
    description='Принудительное обновление всех сделок с Notion -> AmoCRM',
)
def sync_leads_full(background_tasks: BackgroundTasks):
    if red.get('sync-leads-running') is not None:
        return 'Запрос проигнорирован. Процесс полного обновления лидов уже был запущен недавно.'
    red.set('sync-leads-running', '1')
    background_tasks.add_task(NotionService.sync_leads)
    return 'Процесс обновления сделок запущен.'


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
async def process_data(
        request: Request,
        background_tasks: BackgroundTasks,
):
    body_bytes = await request.body()
    body_str = body_bytes.decode('utf-8')
    decoded_data = urllib.parse.parse_qs(body_str)  # noqa
    def process():
        db = next(iter(get_db()))
        try:
            lead = parse_lead_update(decoded_data)
            if lead is not None:
                AMOService(db).process_lead_update_hook(lead)
        finally:
            db.close()
    background_tasks.add_task(process)
    return {
        'success': True
    }


@router.post(
    '/lead-add-item',
    description='Хук для добавления товара к сделке в amoCRM',
)
def lead_add_item(
        body: LeadAddItemRequest,
):
    success = True
    try:
        bt_item = AmoRepo.get_product_by_nid(body.item_nid)
        dt_item = AMODTProduct.from_item(bt_item, int(bt_item.amo_id), body)
        dt_item = AmoRepo.add_dt_product(dt_item)
        AmoRepo.attach_item_to_lead(body.lead_id, dt_item.id, 1)
        AmoRepo.attach_item_to_lead(body.lead_id, dt_item.id, int(body.quantity))
        AmoRepo.attach_item_to_lead(body.lead_id, dt_item.id, int(body.quantity))
    except Exception as ex:
        success = False
        Alert.critical(f'⛔️ Добавление товара: ошибка\nNID: `{body.item_nid}`\n[Сделка:](https://ceh.amocrm.ru/leads/detail/{body.lead_id}) `{body.lead_id}`\n\n{ex}')
    return {
        'success': success,
    }


@router.post(
    '/sync-lead-items',
    description='Хук для синхронизации товаров сделки в amoCRM',
)
def lead_sync_items(
        body: LeadSyncItemsRequest,
        db: SessionLocal = Depends(get_db),
):
    success = True
    try:
        AMOService(db).sync_lead_items(body.lead_id)
    except Exception as ex:
        success = False
        Alert.critical(f'⛔️Ошибка при синхронизация товаров сделки\n'
                       f'[Сделка:](https://ceh.amocrm.ru/leads/detail/{body.lead_id})`'
                       f'\n\n{ex}')
    return {
        'success': success,
    }


@router.post(
    '/item-update',
    description='Хук для обновления товара сделки в amoCRM',
)
async def process_data(request: Request, db: SessionLocal = Depends(get_db)):
    body_bytes = await request.body()
    body_str = body_bytes.decode('utf-8')
    decoded_data = urllib.parse.parse_qs(body_str)  # noqa
    added, updated = parse_dt_product_update(decoded_data)
    try:
        AMOService(db).process_dt_products_update(added, updated)
    except Exception as ex:
        Alert.critical(f'⛔️Ошибка при обновлении товаров сделки:\n\n{ex}')
    return {
        'success': True,
    }
