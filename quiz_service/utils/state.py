import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class QuizStateStore:
    '''
    Маленькая in-memory FSM, заменяющая aiogram FSMContext в quiz_service.
    Ключ -- chat_id. Значение -- словарь со state и data.

    Состояния:
        - 'idle'
        - 'get_ready'   -- послали приглашение, ждем нажатия "готов"
        - 'get_answer'  -- задали вопрос, ждем ответа
    '''

    def __init__(self):
        self._lock = asyncio.Lock()
        self._store: dict[int, dict] = {}

    async def get(self, chat_id: int) -> dict:
        async with self._lock:
            return dict(self._store.get(chat_id, {'state': 'idle', 'data': {}}))

    async def set_state(self, chat_id: int, state: str) -> None:
        async with self._lock:
            entry = self._store.setdefault(chat_id, {'state': 'idle', 'data': {}})
            entry['state'] = state

    async def update_data(self, chat_id: int, **kwargs) -> None:
        async with self._lock:
            entry = self._store.setdefault(chat_id, {'state': 'idle', 'data': {}})
            entry['data'].update(kwargs)

    async def get_data(self, chat_id: int) -> dict:
        async with self._lock:
            return dict(self._store.get(chat_id, {'state': 'idle', 'data': {}}).get('data', {}))

    async def clear(self, chat_id: int) -> None:
        async with self._lock:
            self._store.pop(chat_id, None)


state_store = QuizStateStore()
