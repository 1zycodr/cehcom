from telebot import TeleBot

from app.core import settings


class Alert:

    bot = TeleBot(settings.TG_TOKEN)

    chat_id = -1002236819092
    crit_thread = 2
    tb_thread = 3

    @classmethod
    def critical(cls, message: str):
        cls.bot.send_message(
            cls.chat_id,
            message,
            message_thread_id=cls.crit_thread,
            parse_mode='MarkdownV2',
        )

    @classmethod
    def info(cls, message: str):
        cls.bot.send_message(
            cls.chat_id,
            message,
            message_thread_id=cls.tb_thread,
            parse_mode='MarkdownV2',
        )
