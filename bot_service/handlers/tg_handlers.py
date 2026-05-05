'''
Telegram-handlers. Содержит МИНИМУМ логики: только команды
/start, /restart, /quiz и обработка callback_query.
Вся бизнес-логика -- в quiz_service.
'''

# aiogram
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

# project
from utils.quiz_client import quiz_client

# misc
import logging

logger = logging.getLogger(__name__)
router: Router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    logger.info(f'(username: {message.from_user.username}), '
                f'(chat_id: {message.from_user.id}): /start')

    await quiz_client.event_start(
        chat_id = message.from_user.id,
        username = message.from_user.username or ''
    )


@router.message(Command(commands = 'restart'))
async def cmd_restart(message: Message):
    logger.info(f'(username: {message.from_user.username}), '
                f'(chat_id: {message.from_user.id}): /restart')

    await quiz_client.event_restart(
        chat_id = message.from_user.id,
        username = message.from_user.username or ''
    )


@router.message(Command(commands = 'quiz'))
async def cmd_quiz(message: Message):
    logger.info(f'(username: {message.from_user.username}), '
                f'(chat_id: {message.from_user.id}): /quiz')

    await quiz_client.event_quiz_now(
        chat_id = message.from_user.id,
        username = message.from_user.username or ''
    )


@router.callback_query()
async def any_callback(callback: CallbackQuery):
    '''
    Любой callback просто проксируется в quiz_service.
    Quiz_service сам решит, что делать с этими данными.
    Bot-service отвечает за answer_callback (по запросу quiz_service).
    '''
    logger.info(f'(username: {callback.from_user.username}), '
                f'(chat_id: {callback.from_user.id}): callback={callback.data}')

    await quiz_client.event_callback(
        chat_id = callback.from_user.id,
        message_id = callback.message.message_id,
        callback_id = callback.id,
        username = callback.from_user.username or '',
        data = callback.data or ''
    )
