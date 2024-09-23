# aiogram
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage, Redis

# misc
import logging

logger = logging.getLogger(__name__)

redis = Redis(host = 'localhost')
storage = RedisStorage(redis = redis)
# storage = MemoryStorage()
dp = Dispatcher(storage = storage)

logger.info('Dispatcher started')