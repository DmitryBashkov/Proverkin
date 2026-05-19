from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import logging
from filters.filters import IsExist

# aiogram
from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from service.quiz import check_for_quiz

from database.connector import SQLite3Connector as sqlite3_connector
from service.quiz import schedule_quiz
from utils.schedulers import quiz_scheduler
from utils.misc import get_job


router: Router = Router()

# Initialize the logger
logger = logging.getLogger(__name__)

@router.message(Command(commands = 'quiz'), IsExist())
async def cmd_test(message: Message, bot: Bot, state: FSMContext):
    await check_for_quiz(bot, message.from_user.id)

@router.message(Command(commands='restart'))
async def cmd_restart(message: Message, bot: Bot, state: FSMContext, is_test = False):
    logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): command /restart')

    # Check if the user exists in the database
    user = sqlite3_connector.get_user(username=message.from_user.username, params=['user_id', 'chat_id'])

    if user == None:
        logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): User not found in the database')
        return

    # If the user was added to the database but has no chat_id, they have never written to the bot.
    # We save their chat_id and immediately schedule a quiz.
    if user[1] == None:
        logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): User has no chat_id')
        sqlite3_connector.add_chat_id(message.from_user.username, message.from_user.id)
        logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): added chat_id {message.from_user.id}')

    # Clear state if there was one
    await state.clear()

    # Remove the scheduled job if there was one, and schedule a new one
    existing_job = get_job(message.from_user.username)

    if existing_job != None:
        logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): user has a scheduled quiz {existing_job.id} at {existing_job.next_run_time.strftime("%d.%m at %H:%M")}')
        existing_job.remove()
    
    await schedule_quiz(bot, message.from_user.username, message.from_user.id, True)
