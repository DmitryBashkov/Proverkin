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
    quiz_url: str
    generator_url: str


@dataclass
class Auth:
    admin_user: str
    admin_password: str
    secret_key: str


@dataclass
class BotLogger:
    log_format: str
    path: str
    in_terminal: bool


@dataclass
class Config:
    db: Database
    svc: Service
    auth: Auth
    lg: BotLogger


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
        host = os.environ.get('WEB_HOST', '0.0.0.0'),
        port = int(os.environ.get('WEB_PORT', '8080')),
        quiz_url = os.environ.get('QUIZ_URL', 'http://quiz_service:8001'),
        generator_url = os.environ.get('GENERATOR_URL', 'http://generator_service:8002')
    ),
    auth = Auth(
        admin_user = os.environ.get('WEB_ADMIN_USER', 'admin'),
        admin_password = os.environ.get('WEB_ADMIN_PASSWORD', 'admin'),
        secret_key = os.environ.get('WEB_SECRET_KEY', 'change-me-please')
    ),
    lg = BotLogger(
        log_format = os.environ.get(
            'LOG_FORMAT',
            '%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
        ),
        path = os.environ.get('LOG_PATH', 'logs/web_gui.log'),
        in_terminal = os.environ.get('LOG_IN_TERMINAL', '1') == '1'
    )
)

logging.getLogger(__name__).info('Config объект web_gui создан')
