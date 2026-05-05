# project
from config_data.config import config

# misc
import logging
import requests

logger = logging.getLogger(__name__)


class QuizAdminClient:
    '''Синхронный клиент к quiz_service (web на Flask, поэтому requests).'''

    def __init__(self):
        self.base_url = config.svc.quiz_url.rstrip('/')

    def schedule_user(self, chat_id: int, username: str = None, notify: bool = True) -> dict:
        try:
            r = requests.post(
                f'{self.base_url}/admin/schedule_user',
                json = {'chat_id': chat_id, 'username': username, 'notify': notify},
                timeout = 10
            )
            return r.json()
        except Exception as e:
            logger.error(f'schedule_user failed: {e}')
            return {'status': 'error', 'error': str(e)}


class GeneratorAdminClient:
    def __init__(self):
        self.base_url = config.svc.generator_url.rstrip('/')

    def queue_size(self, set_id: int) -> int:
        try:
            r = requests.get(f'{self.base_url}/queue/{set_id}', timeout = 10)
            return int(r.json().get('pending', 0))
        except Exception as e:
            logger.error(f'queue_size failed: {e}')
            return -1

    def generate_one(self, set_id: int) -> dict:
        try:
            r = requests.post(
                f'{self.base_url}/generate_one',
                json = {'set_id': set_id},
                timeout = 180
            )
            return r.json()
        except Exception as e:
            logger.error(f'generate_one failed: {e}')
            return {'error': str(e)}

    def generate_now(self) -> dict:
        try:
            r = requests.post(f'{self.base_url}/generate_now', json = {}, timeout = 180)
            return r.json()
        except Exception as e:
            logger.error(f'generate_now failed: {e}')
            return {'error': str(e)}


quiz_client = QuizAdminClient()
generator_client = GeneratorAdminClient()
