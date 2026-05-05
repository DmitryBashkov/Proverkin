# project
from config_data.config import config

# misc
import logging
import aiohttp

logger = logging.getLogger(__name__)


class QuizClient:
    '''
    Тонкий HTTP-клиент к quiz_service. Bot-service умеет только
    транслировать события из Telegram в quiz_service, и наоборот --
    отдавать результаты обратно в Telegram.
    '''

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or config.svc.quiz_url).rstrip('/')

    async def _post(self, path: str, payload: dict) -> dict:
        url = f'{self.base_url}{path}'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json = payload, timeout = 30) as resp:
                    data = await resp.json()
                    if resp.status >= 400:
                        logger.error(f'quiz_service {path} -> {resp.status}: {data}')
                    return data
        except Exception as e:
            logger.error(f'quiz_service {path} call failed: {e}')
            return {}

    async def event_start(self, chat_id: int, username: str) -> dict:
        return await self._post('/events/start',
                                {'chat_id': chat_id, 'username': username})

    async def event_restart(self, chat_id: int, username: str) -> dict:
        return await self._post('/events/restart',
                                {'chat_id': chat_id, 'username': username})

    async def event_quiz_now(self, chat_id: int, username: str) -> dict:
        return await self._post('/events/quiz',
                                {'chat_id': chat_id, 'username': username})

    async def event_callback(self, chat_id: int, message_id: int, callback_id: str,
                             username: str, data: str) -> dict:
        return await self._post('/events/callback', {
            'chat_id': chat_id,
            'message_id': message_id,
            'callback_id': callback_id,
            'username': username,
            'data': data
        })


quiz_client = QuizClient()
