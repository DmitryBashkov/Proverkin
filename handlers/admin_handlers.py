# aiogram
from aiogram import Router, Bot
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext

# project
from messages.messages import *
from filters.filters import IsAdmin, IsDocument
from callbacks.edit_callback import CancelEditCallbackFactory
from keyboards.builder import cancel_edit_keyboard
from config_data.config import config
from service.question_editor import Excel
from database.connector import SQLite3Connector as sqlite3_connector
from states.states import EditQuestionsState

# misc
import logging
from os import linesep
import shutil
import datetime


# Initialize the module-level router
router: Router = Router()
router.message.filter(IsAdmin())
logger = logging.getLogger(__name__)
linesep = linesep + '- '

'''
==================================
======== Command handlers ========
==================================
'''

@router.message(Command(commands='edit'))
async def cmd_edit_questions(message: Message, bot: Bot, command: CommandObject, state: FSMContext):
    '''
    
    '''
    logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): request to edit the database')

    # Make a backup of the DB in DD-MM-YY_HH-MM-SS format
    backup_date_stamp =  datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    shutil.copy2(config.db.l_path, f'{config.db.backup_directory}backup_{backup_date_stamp}')

    # Log info about the backup
    logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): backup created - {backup_date_stamp}')

    # Get the user's account_id
    account_id = sqlite3_connector.get_account_id_by_chat_id(message.from_user.id)

    # Save all questions to Excel
    export_file = FSInputFile(Excel.download_questions(account_id))
	
    # Send the file to the user
    await message.answer_document(export_file)

    # Send a cancel button
    await message.answer(text = 'Please send back the updated file', reply_markup = cancel_edit_keyboard())

    # Transition to waiting for the updated file from the user
    await state.set_state(EditQuestionsState.get_updated_file)

    # Store info in state
    await state.update_data(account_id = account_id)

@router.message(Command(commands='add'))
async def cmd_add_questions(message: Message, bot: Bot, command: CommandObject):
    pass

'''
==================================
========= State handlers =========
==================================
'''

@router.message(StateFilter(EditQuestionsState.get_updated_file), IsDocument())
async def get_questions_updates(message: Message, bot: Bot, state: FSMContext):

    # Log that the user sent a file
    logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): user sent a file ({message.document.file_name})')

    # Download the file to the import folder
    await bot.download(file = message.document.file_id, 
                       destination = f'{config.import_file_storage}/{message.document.file_name}')

    # Retrieve information from state
    data = await state.get_data()
    account_id = data['account_id']

    # Update questions in the database
    Excel.upload_questions(account_id, f'{config.import_file_storage}/{message.document.file_name}')

    # Log the update
    logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): data from file ({message.document.file_name}) updated')

    # Notify the user
    await message.answer('Questions updated')

    # Exit state
    await state.clear()

@router.callback_query(CancelEditCallbackFactory.filter(), StateFilter(EditQuestionsState.get_updated_file))
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()
