# project
from config_data.config import config

# misc
import logging
import aiohttp

logger = logging.getLogger(__name__)


class BotClient:
    '''
    Тонкий HTTP-клиент к bot_service. Все, что нам нужно от бота --
    отправлять/редактировать/удалять сообщения и показывать клавиатуры.
    Бизнес-логика и формирование клавиатур остается тут, в quiz_service:
    bot_service просто транслирует payload в Telegram.
    '''

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or config.svc.bot_url).rstrip('/')

    async def _post(self, path: str, payload: dict) -> dict:
        url = f'{self.base_url}{path}'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json = payload, timeout = 30) as resp:
                    data = await resp.json()
                    if resp.status >= 400:
                        logger.error(f'bot_service {path} -> {resp.status}: {data}')
                    return data
        except Exception as e:
            logger.error(f'bot_service {path} call failed: {e}')
            return {}

    async def send_message(self, chat_id: int, text: str,
                           parse_mode: str = 'HTML',
                           reply_markup: dict = None) -> dict:
        return await self._post('/send_message', {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'reply_markup': reply_markup
        })

    async def edit_reply_markup(self, chat_id: int, message_id: int,
                                reply_markup: dict = None) -> dict:
        return await self._post('/edit_reply_markup', {
            'chat_id': chat_id,
            'message_id': message_id,
            'reply_markup': reply_markup
        })

    async def delete_message(self, chat_id: int, message_id: int) -> dict:
        return await self._post('/delete_message', {
            'chat_id': chat_id,
            'message_id': message_id
        })

    async def answer_callback(self, callback_id: str, text: str = None,
                              show_alert: bool = False) -> dict:
        return await self._post('/answer_callback', {
            'callback_id': callback_id,
            'text': text,
            'show_alert': show_alert
        })


bot_client = BotClient()
