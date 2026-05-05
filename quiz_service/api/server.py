'''
HTTP API quiz_service.

Принимает:
  POST /events/start        -- /start от пользователя
  POST /events/restart      -- /restart
  POST /events/quiz         -- /quiz (запустить квиз сейчас)
  POST /events/callback     -- inline-callback из бота
  POST /admin/schedule_user -- запланировать квиз для chat_id (из web-gui)
  GET  /healthz
'''

import logging

from aiohttp import web

from service.quiz import (
    check_for_quiz,
    schedule_quiz,
    handle_ready,
    handle_answer,
)
from service.keyboards import decode_callback
from utils.state import state_store
from utils.misc import get_job
from database.connector import PostgresConnector as pg
from config_data.config import config

logger = logging.getLogger(__name__)


async def health(_request):
    return web.json_response({'status': 'ok'})


async def event_start(request: web.Request):
    body = await request.json()
    chat_id = int(body['chat_id'])
    username = body.get('username') or ''

    logger.info(f'(username: {username}), (chat_id: {chat_id}): /start')

    user = pg.get_user(username = username, chat_id = chat_id,
                       params = ['user_id', 'chat_id'])

    if user is None:
        # пользователя нет в БД -- молча игнорируем (заводим только из web-gui)
        return web.json_response({'status': 'unknown_user'})

    # если у пользователя нет chat_id -- проставляем
    if user[1] is None and username:
        pg.add_chat_id(username, chat_id)
        await schedule_quiz(username, chat_id)
        return web.json_response({'status': 'registered_and_scheduled'})

    # уже есть запланированный квиз?
    if get_job(username):
        return web.json_response({'status': 'already_scheduled'})

    await schedule_quiz(username, chat_id)
    return web.json_response({'status': 'scheduled'})


async def event_restart(request: web.Request):
    body = await request.json()
    chat_id = int(body['chat_id'])
    username = body.get('username') or ''

    logger.info(f'(username: {username}), (chat_id: {chat_id}): /restart')

    user = pg.get_user(username = username, chat_id = chat_id,
                       params = ['user_id', 'chat_id'])
    if user is None:
        return web.json_response({'status': 'unknown_user'})

    if user[1] is None and username:
        pg.add_chat_id(username, chat_id)

    await state_store.clear(chat_id)

    existing = get_job(username)
    if existing is not None:
        existing.remove()

    await schedule_quiz(username, chat_id, notify = True)
    return web.json_response({'status': 'rescheduled'})


async def event_quiz_now(request: web.Request):
    body = await request.json()
    chat_id = int(body['chat_id'])

    if not pg.is_exist(chat_id):
        return web.json_response({'status': 'unknown_user'})

    await check_for_quiz(chat_id)
    return web.json_response({'status': 'started'})


async def event_callback(request: web.Request):
    '''
    Получаем inline-callback от bot_service.
    Тело: {chat_id, message_id, callback_id, username, data}
    '''
    body = await request.json()

    chat_id = int(body['chat_id'])
    message_id = int(body['message_id'])
    callback_id = str(body['callback_id'])
    username = body.get('username') or ''
    data = str(body.get('data', ''))

    ns, payload = decode_callback(data)

    if ns == 'ready':
        await handle_ready(chat_id, message_id, callback_id)
        return web.json_response({'status': 'ok'})

    if ns == 'quiz':
        await handle_answer(chat_id, message_id, callback_id, username, payload)
        return web.json_response({'status': 'ok'})

    logger.warning(f'unknown callback ns={ns}, data={data}')
    return web.json_response({'status': 'unknown_callback'})


async def admin_schedule_user(request: web.Request):
    body = await request.json()
    chat_id = int(body['chat_id'])
    username = body.get('username') or pg.get_user_by_chat_id(chat_id)
    if not username:
        return web.json_response({'status': 'unknown_user'}, status = 400)

    await schedule_quiz(username, chat_id, notify = bool(body.get('notify', True)))
    return web.json_response({'status': 'scheduled'})


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_get('/healthz', health)
    app.router.add_post('/events/start', event_start)
    app.router.add_post('/events/restart', event_restart)
    app.router.add_post('/events/quiz', event_quiz_now)
    app.router.add_post('/events/callback', event_callback)
    app.router.add_post('/admin/schedule_user', admin_schedule_user)
    return app
