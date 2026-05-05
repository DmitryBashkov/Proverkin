# project
from config_data.config import config
from utils.schedulers import quiz_scheduler
from database.connector import PostgresConnector as pg
from service.quiz import reschedule_all_active_users
from api.server import build_app

# misc
import asyncio
import logging
from logging import handlers
import os

from aiohttp import web


# ====== логирование ======
os.makedirs(os.path.dirname(config.lg.path), exist_ok = True)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = handlers.TimedRotatingFileHandler(
    config.lg.path, when = 'midnight', interval = 1
)
file_handler.setFormatter(logging.Formatter(config.lg.log_format))
logger.addHandler(file_handler)

if config.lg.in_terminal:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(config.lg.log_format))
    logger.addHandler(stream_handler)

logger.info('Quiz service starting')


async def on_startup(app: web.Application):
    # ждем готовности БД (compose уже стартует postgres первым,
    # но init.sql может еще выполняться)
    for attempt in range(30):
        if pg.init_check():
            break
        logger.info(f'Postgres еще не готов, попытка {attempt + 1}/30')
        await asyncio.sleep(2)
    else:
        raise RuntimeError('Postgres недоступен или init.sql не отработал')

    quiz_scheduler.start()

    total = await reschedule_all_active_users()
    logger.info(f'Запланированы квизы для {total} пользователей')


async def on_cleanup(app: web.Application):
    if quiz_scheduler.running:
        quiz_scheduler.shutdown(wait = False)


def main():
    app = build_app()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    web.run_app(app, host = config.svc.host, port = config.svc.port)


if __name__ == '__main__':
    main()
