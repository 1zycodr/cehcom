import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utilities import repeat_every

from app.core import settings
from app.core.config import red
from app.core.middleware import catch_exceptions_middleware
from app.job.sync import sync_notion_amo, sync_notion_leads
from app.api.v1.router import api_router as v1_router
from app.repository.tgbot import Alert

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


@app.on_event('startup')
@repeat_every(seconds=60, wait_first=True)
def sync():
    if red.get('sync-running') is not None:
        print('sync already running')
        return
    red.set('sync-running', '1')
    sync_notion_amo()


@app.on_event('startup')
@repeat_every(seconds=10, wait_first=True)
def sync_leads():
    if red.get('sync-leads-running') is not None:
        print('sync leads already running')
        return
    red.set('sync-leads-running', '1')
    sync_notion_leads()


@app.on_event('shutdown')
def shutdown():
    Alert.critical('`🛑 Сервер остановлен.`')


if __name__ == "__main__":
    Alert.critical('`🟢 Сервер запущен.`')
    red.delete('sync-running')
    red.delete('sync-leads-running')
    uvicorn.run("app.main:app", host='0.0.0.0', port=8000)
