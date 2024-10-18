import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utilities import repeat_every

from app.core import settings
from app.core.config import red
from app.core.middleware import catch_exceptions_middleware
from app.job.sync import sync_notion_amo, sync_notion_leads
from app.api.v1.router import api_router as v1_router
from app.repository.amocrm import AmoRepo
from app.repository.tgbot import Alert
from app.repository.wordpress import WordpressRepository
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


# @app.on_event('startup')
# @repeat_every(seconds=10, wait_first=True)
# def sync():
#     if red.get('sync-running') is not None:
#         print('sync already running')
#         return
#     red.set('sync-running', '1')
#     sync_notion_amo()
#
#
# @app.on_event('startup')
# @repeat_every(seconds=10, wait_first=True)
# def sync_leads():
#     if red.get('sync-leads-running') is not None:
#         print('sync leads already running')
#         return
#     red.set('sync-leads-running', '1')
#     sync_notion_leads()
#
#
# @app.on_event('startup')
# def sync_notion_wp():
#     if red.get('sync-wp-items-running') is not None:
#         print('sync wp items already running')
#         return
#     red.set('sync-wp-items-running', '1')
#     sync_wp_items()


@app.on_event('shutdown')
def shutdown():
    Alert.critical('`🛑 Сервер остановлен.`')


if __name__ == "__main__":
    # Alert.critical('`🟢 Сервер запущен.`')
    # red.delete('sync-running')
    # red.delete('sync-leads-running')
    # red.delete('sync-wp-items-running')
    # uvicorn.run("app.main:app", host='0.0.0.0', port=8000)
    NotionService.sync_with_amo(True)
    # AmoRepo.delete_from_catalog(['919727'])
    # data = {
    #     "name": "Premium Quality",
    #     "type": "simple",
    #     "regular_price": "21.99",
    #     "description": "Pellentesque habitant morbi tristique senectus et netus "
    #                    "et malesuada fames ac turpis egestas. Vestibulum tortor quam, "
    #                    "feugiat vitae, ultricies eget, tempor sit amet, ante. Donec eu "
    #                    "libero sit amet quam egestas semper. Aenean ultricies mi vitae est. "
    #                    "Mauris placerat eleifend leo.",
    #     "short_description": "Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas.",
    #     "images": [
    #         {
    #             "src": "https://api.cehcom.kz/media/02036.jpg"
    #         }
    #     ],
    #     "attributes": [
    #         {
    #             'id': 9,
    #             'options': ['12345'],
    #         }
    #     ]
    # }
    # WordpressRepository.add_product(data)
    WordpressRepository.get_all_products()
