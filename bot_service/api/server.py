'''
HTTP API bot_service.

Endpoints для quiz_service:
    POST /send_message
    POST /edit_reply_markup
    POST /delete_message
    POST /answer_callback

Endpoint для Telegram:
    POST /telegram/webhook  (плюс secret-token проверка)

Сервисный:
    GET  /healthz
'''

import logging

from aiogram.types import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.exceptions import TelegramAPIError
from aiohttp import web

from config_data.config import config

logger = logging.getLogger(__name__)


def _build_markup(payload: dict | None) -> InlineKeyboardMarkup | None:
    '''
    Превращает payload из quiz_service в InlineKeyboardMarkup.

    Ожидаемый формат:
        {"rows": [[{"text": "...", "callback_data": "..."}], ...]}
    '''
    if not payload:
        return None
    rows_payload = payload.get('rows') or []
    rows = []
    for row in rows_payload:
        rows.append([
            InlineKeyboardButton(
                text = btn['text'],
                callback_data = btn.get('callback_data', '')
            )
            for btn in row
        ])
    return InlineKeyboardMarkup(inline_keyboard = rows)


async def health(_request):
    return web.json_response({'status': 'ok'})


async def send_message(request: web.Request):
    body = await request.json()
    bot = request.app['bot']
    try:
        msg = await bot.send_message(
            chat_id = body['chat_id'],
            text = body['text'],
            parse_mode = body.get('parse_mode', 'HTML'),
            reply_markup = _build_markup(body.get('reply_markup'))
        )
        return web.json_response({
            'message_id': msg.message_id,
            'chat_id': msg.chat.id
        })
    except TelegramAPIError as e:
        logger.error(f'send_message: {e}')
        return web.json_response({'error': str(e)}, status = 500)


async def edit_reply_markup(request: web.Request):
    body = await request.json()
    bot = request.app['bot']
    try:
        await bot.edit_message_reply_markup(
            chat_id = body['chat_id'],
            message_id = body['message_id'],
            reply_markup = _build_markup(body.get('reply_markup'))
        )
        return web.json_response({'status': 'ok'})
    except TelegramAPIError as e:
        # это часто случается при попытке редактировать одно и то же
        logger.warning(f'edit_reply_markup: {e}')
        return web.json_response({'status': 'error', 'error': str(e)})


async def delete_message(request: web.Request):
    body = await request.json()
    bot = request.app['bot']
    try:
        await bot.delete_message(
            chat_id = body['chat_id'],
            message_id = body['message_id']
        )
        return web.json_response({'status': 'ok'})
    except TelegramAPIError as e:
        logger.warning(f'delete_message: {e}')
        return web.json_response({'status': 'error', 'error': str(e)})


async def answer_callback(request: web.Request):
    body = await request.json()
    bot = request.app['bot']
    try:
        await bot.answer_callback_query(
            callback_query_id = body['callback_id'],
            text = body.get('text'),
            show_alert = bool(body.get('show_alert', False))
        )
        return web.json_response({'status': 'ok'})
    except TelegramAPIError as e:
        logger.warning(f'answer_callback: {e}')
        return web.json_response({'status': 'error', 'error': str(e)})


async def telegram_webhook(request: web.Request):
    # проверка секрета (Telegram ставит этот заголовок при secret_token)
    expected = config.tg_bot.webhook_secret
    if expected:
        actual = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if actual != expected:
            logger.warning('Bad webhook secret')
            return web.json_response({'status': 'forbidden'}, status = 403)

    body = await request.json()
    bot = request.app['bot']
    dp = request.app['dp']

    try:
        update = Update.model_validate(body, context = {'bot': bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f'webhook processing failed: {e}')

    return web.json_response({'status': 'ok'})


def build_app(bot, dp) -> web.Application:
    app = web.Application()
    app['bot'] = bot
    app['dp'] = dp

    app.router.add_get('/healthz', health)
    app.router.add_post('/send_message', send_message)
    app.router.add_post('/edit_reply_markup', edit_reply_markup)
    app.router.add_post('/delete_message', delete_message)
    app.router.add_post('/answer_callback', answer_callback)
    app.router.add_post('/telegram/webhook', telegram_webhook)

    return app
