from dataclasses import dataclass
import logging
import os
from dotenv import load_dotenv
import json

@dataclass
class TgBot:
    token: str             # Токен для доступа к телеграм-боту

@dataclass
class GCredentials:
    google_service_account: str
    json_config: str

@dataclass
class BotLogger:
    log_format: str
    path: str
    rotation_time: str
    rotation_interval: int
    in_terminal: bool

@dataclass
class Database:
    l_path: str
    r_host: str
    r_user: str
    r_password: str
    r_database: str
    backup_directory: str

@dataclass
class Config:
    tg_bot: TgBot
    gc: GCredentials
    db: Database
    lg: BotLogger
    export_file_storage: str
    import_file_storage: str
    yandex_gpt_api: str

'''
======== загружаем данные из .env: токен бота и путь к файлу конфигурации ========
'''

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f'Конфигурация {dotenv_path} загружена')
else:
    print(f'Не удалось загрузить {dotenv_path} конфигурацию')


'''
======== загружаем данные из файла кофигурации (config.json) ========
'''
json_data = None
try:
    with open(os.environ.get('BOT_CONFIG'), 'r') as jsonfile:
        json_data = json.load(jsonfile)
except FileNotFoundError as error:
    print(f'Не удалось загрузить {os.environ.get("BOT_CONFIG")} конфигураци\n'
                f'Ошибка: {error}')
else:
    print(f'Конфигурация {os.environ.get("BOT_CONFIG")} загружена')


'''
======== создаем объект кофигурации ========
'''


config = Config(
        tg_bot = TgBot(
            token = os.environ.get('QUICK_QUIZ_BOT_TOKEN')),
        gc = GCredentials(
            google_service_account = os.environ.get('GOOGLE_SERVICE_ACCOUNT'),
            json_config = os.environ.get('JSON_CONFIG')),
        db = Database(
            l_path = json_data['database']['local']['path'],
            backup_directory = json_data['database']['local']['backup_directory'],
            r_host = json_data['database']['remote']['host'],
            r_user = json_data['database']['remote']['user'],
            r_password = os.environ.get('REMOTE_DB_PASSWORD'),
            r_database = json_data['database']['remote']['database']
        ),
        lg = BotLogger(
            log_format = json_data['logger']['log_format'],
            path = json_data['logger']['path'],
            rotation_time = json_data['logger']['rotation_time'],
            rotation_interval = json_data['logger']['rotation_interval'],
            in_terminal = os.environ.get('LOG_IN_TERMINAL')
        ),
        export_file_storage = json_data['export_file_storage'],
        import_file_storage = json_data['import_file_storage'],
        yandex_gpt_api = os.environ.get('YANDEX_GPT_API')
    )

if config != None:
    print('Объект кофигурации создан')
else:
    print(('Объект кофигурации не создан'))
