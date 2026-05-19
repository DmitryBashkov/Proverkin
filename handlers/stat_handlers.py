# aiogram
from aiogram import Router, Bot
from aiogram.types import CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, CallbackQuery


# project
from service.user import User
from service.stat_operations import get_day_stat, get_week_stat, get_failed_questions
from messages.messages import *
from callbacks.stat_callback import StatCallbackFactory
from config_data.const import STAT_MODES

# misc
import logging
from os import linesep

# Initialize the module-level router
router: Router = Router()

# Initialize the logger
logger = logging.getLogger(__name__)

linesep = linesep + '- '

@router.message(Command(commands='stat'))
async def cmd_get_stat(message: Message, bot: Bot, command: CommandObject):
    user = command.args
    if user == None:
        user = 'all'

    keyboard = InlineKeyboardBuilder()
    for mode in STAT_MODES:
        keyboard.button(text = STAT_MODES[mode], callback_data = StatCallbackFactory(user = user, mode = mode))

    keyboard.adjust(1)
    
    await message.answer(text = 'Which statistics are you interested in?',
                         reply_markup = keyboard.as_markup())

@router.callback_query(StatCallbackFactory.filter())
async def get_stat(callback: CallbackQuery, callback_data: StatCallbackFactory, bot: Bot):
    await callback.message.delete_reply_markup()
    user = User(callback.from_user.username)
    user_stat = callback_data.user
    
    # Check which statistics the user requested
    match callback_data.mode:

        # daily statistics
        case 'day_stat':
            file_to_send = get_day_stat(user = user, user_stat = user_stat)
            if file_to_send == False:
                await bot.send_message(chat_id = user.chat_id,
                                       text = 'No data for today')
            else:
                await bot.send_photo(chat_id = user.chat_id, 
                                    photo = file_to_send)
        
        # weekly statistics
        case 'week_stat':
            file_to_send = get_week_stat(user = user, user_stat = user_stat)
            if file_to_send == False:
                await bot.send_message(chat_id = user.chat_id,
                                       text = 'No data for today')
            else:
                await bot.send_photo(chat_id = user.chat_id, 
                                           photo = file_to_send)
        
        # statistics for questions with the most incorrect answers
        case 'failed_questions':
            msg_text: str = ''
            question_list = get_failed_questions(user = user, user_stat = user_stat)
            for question in question_list:
                msg_text += f'<b>{question[0]}</b>\n<i>({question[1]} incorrect)</i>\n\n'
            await bot.send_message(chat_id = user.chat_id,
                                   text = msg_text,
                                   parse_mode = 'HTML')
