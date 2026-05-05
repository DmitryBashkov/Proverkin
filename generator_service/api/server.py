'''
HTTP API generator_service. Минималистичный.

  GET  /healthz
  POST /generate_now      -- принудительный прогон одного цикла
  POST /generate_one      -- сгенерить один вопрос для конкретного set_id
  GET  /queue/{set_id}    -- сколько вопросов в pending в очереди
'''

import logging

from aiohttp import web

from config_data.config import config
from database.connector import PostgresConnector as pg
from service.openrouter import openrouter_client
from service.worker import replenish_once

logger = logging.getLogger(__name__)


async def health(_request):
    return web.json_response({'status': 'ok'})


async def generate_now(request: web.Request):
    body = {}
    if request.body_exists:
        try:
            body = await request.json()
        except Exception:
            body = {}
    batch = int(body.get('batch_size', config.generator.batch_size))
    generated = await replenish_once(batch_size = batch)
    return web.json_response({'generated': generated})


async def generate_one(request: web.Request):
    body = await request.json()
    set_id = int(body['set_id'])

    sets = pg.get_generator_sets()
    target = next((s for s in sets if s[0] == set_id), None)
    if target is None:
        return web.json_response(
            {'error': f'set_id {set_id} не настроен на генерацию'},
            status = 400
        )

    _, account_id, _, prompt, model, _ = target
    payload = await openrouter_client.generate_question(prompt, model)
    if not payload:
        return web.json_response({'error': 'generation failed'}, status = 502)

    item_id = pg.queue_push(set_id, account_id, payload,
                            model or config.openrouter.default_model)
    return web.json_response({'item_id': item_id, 'payload': payload})


async def queue_size(request: web.Request):
    set_id = int(request.match_info['set_id'])
    return web.json_response({
        'set_id': set_id,
        'pending': pg.queue_pending_count(set_id)
    })


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_get('/healthz', health)
    app.router.add_post('/generate_now', generate_now)
    app.router.add_post('/generate_one', generate_one)
    app.router.add_get('/queue/{set_id}', queue_size)
    return app
