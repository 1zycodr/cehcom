import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utilities import repeat_every

from app.core import settings
from app.core.config import red
from app.core.middleware import catch_exceptions_middleware
from app.job.sync import sync_notion_amo
from app.api.v1.router import api_router as v1_router
from app.services import NotionService

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


if __name__ == "__main__":
    red.delete('sync-running')
    uvicorn.run("app.main:app", host='0.0.0.0', port=8000)
