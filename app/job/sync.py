from app.services import NotionService


def sync_notion_amo():
    NotionService.sync_with_amo()
