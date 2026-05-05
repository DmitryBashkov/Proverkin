# aiogram
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# project
from config_data.config import config
from handlers import tg_handlers
from api.server import build_app

# misc
import logging
from logging import handlers
import os
import asyncio

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

logger.info('Bot service starting')


async def on_startup(app: web.Application):
    bot: Bot = app['bot']

    main_menu_commands = [
        BotCommand(command = '/quiz',
                   description = 'Запустить квиз прямо сейчас'),
        BotCommand(command = '/restart',
                   description = 'Если что-то пошло не так и вы перестали получать запланированные квизы'),
    ]
    await bot.set_my_commands(main_menu_commands)

    if config.tg_bot.webhook_url:
        await bot.set_webhook(
            url = config.tg_bot.webhook_url,
            secret_token = config.tg_bot.webhook_secret,
            drop_pending_updates = True
        )
        logger.info(f'Webhook установлен на {config.tg_bot.webhook_url}')
    else:
        logger.warning('TG_WEBHOOK_URL не задан -- работаем как HTTP API без подписки на Telegram')


async def on_cleanup(app: web.Application):
    bot: Bot = app['bot']
    try:
        await bot.delete_webhook(drop_pending_updates = False)
    except Exception:
        pass
    await bot.session.close()


def main():
    bot = Bot(
        token = config.tg_bot.token,
        default = DefaultBotProperties(parse_mode = ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(tg_handlers.router)

    app = build_app(bot, dp)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    web.run_app(app, host = config.svc.host, port = config.svc.port)


if __name__ == '__main__':
    main()
