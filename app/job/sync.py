from app.core.logger import get_logger
from app.services import NotionService

log = get_logger()


def sync_notion_amo():
    log.warn('start job sync_notion_amo')
    NotionService.sync_with_amo()
