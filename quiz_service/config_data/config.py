from dataclasses import dataclass
import os
import logging

from dotenv import load_dotenv

@dataclass
class Database:
    dsn: str

@dataclass
class Service:
    host: str
    port: int
    bot_url: str            # http://bot_service:8000
    generator_url: str      # http://generator_service:8002

@dataclass
class BotLogger:
    log_format: str
    path: str
    in_terminal: bool

@dataclass
class Quiz:
    quiz_start_hour: int
    quiz_end_hour: int
    timezone: str

@dataclass
class Config:
    db: Database
    svc: Service
    lg: BotLogger
    quiz: Quiz


# .env загружается опционально -- в docker-compose все придет через environment
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


config = Config(
    db = Database(
        dsn = os.environ.get(
            'POSTGRES_DSN',
            'postgresql://proverkin:proverkin@postgres:5432/proverkin'
        )
    ),
    svc = Service(
        host = os.environ.get('QUIZ_HOST', '0.0.0.0'),
        port = int(os.environ.get('QUIZ_PORT', '8001')),
        bot_url = os.environ.get('BOT_URL', 'http://bot_service:8000'),
        generator_url = os.environ.get('GENERATOR_URL', 'http://generator_service:8002')
    ),
    lg = BotLogger(
        log_format = os.environ.get(
            'LOG_FORMAT',
            '%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
        ),
        path = os.environ.get('LOG_PATH', 'logs/quiz_service.log'),
        in_terminal = os.environ.get('LOG_IN_TERMINAL', '1') == '1'
    ),
    quiz = Quiz(
        quiz_start_hour = int(os.environ.get('QUIZ_START_HOUR', '10')),
        quiz_end_hour = int(os.environ.get('QUIZ_END_HOUR', '11')),
        timezone = os.environ.get('TZ', 'Europe/Moscow')
    )
)

logging.getLogger(__name__).info('Config объект quiz_service создан')
