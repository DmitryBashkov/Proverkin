from dataclasses import dataclass
import os
import logging

from dotenv import load_dotenv


@dataclass
class TgBot:
    token: str
    webhook_url: str        # https://example.com/telegram/webhook
    webhook_secret: str     # X-Telegram-Bot-Api-Secret-Token


@dataclass
class Service:
    host: str
    port: int
    quiz_url: str           # http://quiz_service:8001


@dataclass
class BotLogger:
    log_format: str
    path: str
    in_terminal: bool


@dataclass
class Config:
    tg_bot: TgBot
    svc: Service
    lg: BotLogger


dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


config = Config(
    tg_bot = TgBot(
        token = os.environ.get('TG_BOT_TOKEN', ''),
        webhook_url = os.environ.get('TG_WEBHOOK_URL', ''),
        webhook_secret = os.environ.get('TG_WEBHOOK_SECRET', 'proverkin-secret')
    ),
    svc = Service(
        host = os.environ.get('BOT_HOST', '0.0.0.0'),
        port = int(os.environ.get('BOT_PORT', '8000')),
        quiz_url = os.environ.get('QUIZ_URL', 'http://quiz_service:8001')
    ),
    lg = BotLogger(
        log_format = os.environ.get(
            'LOG_FORMAT',
            '%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
        ),
        path = os.environ.get('LOG_PATH', 'logs/bot_service.log'),
        in_terminal = os.environ.get('LOG_IN_TERMINAL', '1') == '1'
    )
)

logging.getLogger(__name__).info('Config объект bot_service создан')
