from time import sleep

from app.services import NotionService


def sync_notion_amo():
    print('start job')
    NotionService.sync_with_amo()
