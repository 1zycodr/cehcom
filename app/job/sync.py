from app.core.logger import get_logger
from app.repository.tgbot import Alert
from app.services import NotionService

log = get_logger()


def sync_notion_amo():
    log.warn('start job sync_notion_amo')
    NotionService.sync_with_amo()


def sync_notion_leads():
    log.warn('start job sync_notion_leads')
    NotionService.sync_leads()
