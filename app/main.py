import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core import settings
from app.core.middleware import catch_exceptions_middleware
from app.job.sync import sync_notion_amo
from app.services import NotionService
from app.api.v1.router import api_router as v1_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=settings.OPENAPI_JSON_URL,
    docs_url=settings.DOCS_URL,
)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix=settings.API_V1_STR)

# Enable exception handling middleware.py
if settings.ENVIRONMENT != settings.Environment.local.value:
    app.middleware('http')(catch_exceptions_middleware)

scheduler = BackgroundScheduler()
scheduler.start()

scheduler.add_job(
    sync_notion_amo,
    trigger=IntervalTrigger(minutes=1),
    id='sync_notion_amo',
    replace_existing=False,
    max_instances=1,
)

if __name__ == "__main__":

    # алгоритм
    # запрос данных с notion, который запрашивает по updated_at и статус не "Резерв"
    # обновление данных построчно - полный update строки в amocrm
    # если статус каталога "удалить":
    #   1) удаляем из amo
    #   2) изменяем статус на "удалено из таблицы" в amo
    # data = AmoRepo.get_all_products()
    # NotionService.sync_with_amo()

    uvicorn.run("app.main:app", host='0.0.0.0', port=8000)
