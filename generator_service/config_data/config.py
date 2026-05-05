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


@dataclass
class OpenRouter:
    api_key: str
    base_url: str
    default_model: str
    referer: str
    title: str


@dataclass
class Generator:
    poll_interval_sec: int
    batch_size: int


@dataclass
class BotLogger:
    log_format: str
    path: str
    in_terminal: bool


@dataclass
class Config:
    db: Database
    svc: Service
    openrouter: OpenRouter
    generator: Generator
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
        host = os.environ.get('GENERATOR_HOST', '0.0.0.0'),
        port = int(os.environ.get('GENERATOR_PORT', '8002'))
    ),
    openrouter = OpenRouter(
        api_key = os.environ.get('OPENROUTER_API_KEY', ''),
        base_url = os.environ.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1'),
        default_model = os.environ.get('OPENROUTER_MODEL', 'openai/gpt-4o-mini'),
        referer = os.environ.get('OPENROUTER_REFERER', 'https://github.com/DmitryBashkov/Proverkin'),
        title = os.environ.get('OPENROUTER_TITLE', 'Proverkin')
    ),
    generator = Generator(
        poll_interval_sec = int(os.environ.get('GEN_POLL_INTERVAL', '60')),
        batch_size = int(os.environ.get('GEN_BATCH_SIZE', '3'))
    ),
    lg = BotLogger(
        log_format = os.environ.get(
            'LOG_FORMAT',
            '%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
        ),
        path = os.environ.get('LOG_PATH', 'logs/generator_service.log'),
        in_terminal = os.environ.get('LOG_IN_TERMINAL', '1') == '1'
    )
)

logging.getLogger(__name__).info('Config объект generator_service создан')
