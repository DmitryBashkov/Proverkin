from dataclasses import dataclass
import logging
import os
from dotenv import load_dotenv
import json

@dataclass
class TgBot:
    token: str             # Token for accessing the Telegram bot

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
======== Load data from .env: bot token and path to config file ========
'''

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f'Configuration {dotenv_path} loaded')
else:
    print(f'Failed to load {dotenv_path} configuration')


'''
======== Load data from config file (config.json) ========
'''
json_data = None
try:
    with open(os.environ.get('BOT_CONFIG'), 'r') as jsonfile:
        json_data = json.load(jsonfile)
except FileNotFoundError as error:
    print(f'Failed to load {os.environ.get("BOT_CONFIG")} configuration\n'
                f'Error: {error}')
else:
    print(f'Configuration {os.environ.get("BOT_CONFIG")} loaded')


'''
======== Create the configuration object ========
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
    print('Configuration object created')
else:
    print(('Configuration object not created'))
