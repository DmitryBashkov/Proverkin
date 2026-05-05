# project
from config_data.config import config
from database.connector import PostgresConnector as pg
from service.worker import replenish_loop
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

logger.info('Generator service starting')


async def on_startup(app: web.Application):
    for attempt in range(30):
        if pg.init_check():
            break
        logger.info(f'Postgres еще не готов, попытка {attempt + 1}/30')
        await asyncio.sleep(2)
    else:
        raise RuntimeError('Postgres недоступен или init.sql не отработал')

    # запускаем фоновый воркер
    app['replenish_task'] = asyncio.create_task(replenish_loop())


async def on_cleanup(app: web.Application):
    task = app.get('replenish_task')
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def main():
    app = build_app()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    web.run_app(app, host = config.svc.host, port = config.svc.port)


if __name__ == '__main__':
    main()
