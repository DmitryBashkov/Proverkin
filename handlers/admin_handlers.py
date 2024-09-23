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


# Инициализируем роутер уровня модуля
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
    logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): запрос на редактирование БД')

    # делаем бэкап БД в формате ДД-ММ-ГГ_ЧЧ-ММ-СС
    backup_date_stamp =  datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    shutil.copy2(config.db.l_path, f'{config.db.backup_directory}backup_{backup_date_stamp}')

    # заносим в лог инормациф о бекапе
    logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): создан бэкап - {backup_date_stamp}')

    # получаем account_id пользователя
    account_id = sqlite3_connector.get_account_id_by_chat_id(message.from_user.id)

    # сохраняем все вопросы в эксель
    export_file = FSInputFile(Excel.download_questions(account_id))
		
    # отправляем файл пользователю
    await message.answer_document(export_file)

    # отправляем кнопку отмены
    await message.answer(text = 'Отправьте обратно обновленный файл', reply_markup = cancel_edit_keyboard())

    # переходим в ожидание обновленного файла от пользователя
    await state.set_state(EditQuestionsState.get_updated_file)

    # заносим инфу в state
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

    # заносим в логи, что пользователь прислал файл
    logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): пользователь прислал файл ({message.document.file_name})')

    # загружаем файл в папку с импортом
    await bot.download(file = message.document.file_id, 
                       destination = f'{config.import_file_storage}/{message.document.file_name}')

    # получаем информацию из state 
    data = await state.get_data()
    account_id = data['account_id']

    # обновляем вопросы в БД
    Excel.upload_questions(account_id, f'{config.import_file_storage}/{message.document.file_name}')

    # заноси в логи
    logger.info(f'(username: {message.from_user.username}), (chat_id: {message.from_user.id}): данные из файла ({message.document.file_name}) обновлены')

    # оповещаем пользователя
    await message.answer('Вопросы обновлены')

    # выходим из state
    await state.clear()

@router.callback_query(CancelEditCallbackFactory.filter(), StateFilter(EditQuestionsState.get_updated_file))
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()

