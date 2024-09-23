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

# инициализируем логгер
logger = logging.getLogger(__name__)

@router.message(Command(commands = 'quiz'), IsExist())
async def cmd_test(message: Message, bot: Bot, state: FSMContext):
    await check_for_quiz(bot, message.from_user.id)

@router.message(Command(commands='restart'))
async def cmd_restart(message: Message, bot: Bot, state: FSMContext, is_test = False):
    logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): команда /restart')

    #проверяем, если ли юзер в бд
    user = sqlite3_connector.get_user(message.from_user.username)

    if user == None:
        logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): Пользователя нет в бд')
        return

    # если пользователя внесли в базу, нет chat_id, значит он еще ни разу не писал в бот.
    # мы записываем его chat_id и сразу назначаем квиз
    if user[1] == None:
        logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): У пользователя нет chat_id')
        sqlite3_connector.add_chat_id(message.from_user.username, message.from_user.id)
        logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): добавили chat_id {message.from_user.id}')

    # убираем state если он был
    await state.clear()

    # удаляем задачу из планировщика, если такая была, и ставим новую
    existing_job = get_job(quiz_scheduler.get_jobs(), message.from_user.username)

    if existing_job != None:
        logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): у пользователя есть запланированный квиз {existing_job.id} на {existing_job.next_run_time.strftime("%d.%m в %H:%M")}')
        existing_job.remove()
    
    await schedule_quiz(bot, message.from_user.username, message.from_user.id, True)
