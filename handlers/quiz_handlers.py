# aiogram
from aiogram import Router, Bot
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

# project
from service.quiz import send_question, start_quiz, schedule_quiz
from callbacks.quiz_callback import (
    ReadyCallbackFactory, 
    QuizCallbackFactory
)
from callbacks.score_gpt_callback import GPTScoreCallbackFactory
from states.states import QuizState
from messages.messages import *
from database.connector import SQLite3Connector as sqlite3_connector
from database.connector import MySQLConnector as mysql_connector
from utils.misc import get_job
from utils.schedulers import quiz_scheduler

# misc
import logging
import datetime
import random
from os import linesep
import time


# Initialize the module-level router
router: Router = Router()

# Initialize the logger
logger = logging.getLogger(__name__)
linesep = linesep + '- '
  
@router.callback_query(ReadyCallbackFactory.filter(), StateFilter(QuizState.get_ready))
async def get_ready(callback: CallbackQuery, state: FSMContext, callback_data = ReadyCallbackFactory):
    await callback.message.delete_reply_markup()
    await start_quiz(callback._bot, state)

@router.callback_query(QuizCallbackFactory.filter(), StateFilter(QuizState.get_answer))
async def get_answer(callback: CallbackQuery, bot: Bot, callback_data = QuizCallbackFactory, state = FSMContext):

    end_time = time.time()

    logging.info(f'{callback.from_user.username}: received answer from user, index = {callback_data}')
    
    # Get the question itself and the question list
    data = await state.get_data()
    
    chat_id = data['chat_id']
    question_id = data['question_id']
    start_time = data['start_time']
    answer = None

    # check if user reports about incorrect question
    if callback_data.incorrect_question:
        await callback.message.answer(f'Thank you, we have noted that!')
        sqlite3_connector.update_question_type(callback_data.question_id, 'incorrect')

    # if question correct we check answer
    else:


        answer = sqlite3_connector.get_answers(answer_id = callback_data.id_)[0][0]

        # Check if the user's answer is correct

        if callback_data.right:
            await callback.answer(text = '✅ ' + random.choice(CONGRATS), show_alert = True)
            await callback.message.answer(f"✅ {answer}")
            await callback.message.delete_reply_markup()

        else:
            await callback.answer(text = '❌ ' + random.choice(WRONG), show_alert = True)
            await callback.message.answer(f'❌ {answer}')
            await callback.message.answer(f"Correct answer: {sqlite3_connector.get_answers(question_id = question_id, right = True)[0][0]}")
            await callback.message.delete_reply_markup()

    mysql_connector.add_log([
            datetime.datetime.now().strftime('%Y-%m-%d'),
            *sqlite3_connector.get_log_data(question_id, chat_id),
            int(callback_data.right),
            answer,
            end_time - start_time
        ])

    randomized_question_list = data['randomized_question_list']
    randomized_question_list.pop(0)
    
    # Check if the user has any questions remaining
    if len(randomized_question_list) == 0: 
        # await schedule_next_quiz(message)
        username = sqlite3_connector.get_user_by_chat_id(chat_id)
        logging.info(f'(username: {username}), (chat_id: {chat_id}): Finishing the quiz')
        await callback.message.answer(f'Quiz finished! Well done! 💪')
        if not get_job(callback.from_user.username):
            await schedule_quiz(bot, callback.from_user.username, chat_id)
        await state.clear()


    else:
        await state.update_data(randomized_question_list = randomized_question_list)
        await send_question(bot, state)


@router.callback_query(GPTScoreCallbackFactory.filter(), StateFilter(QuizState.get_answer))
async def get_gpt_score(callback: CallbackQuery, bot: Bot, callback_data = GPTScoreCallbackFactory, state = FSMContext):
    score = callback_data.score

    data = await state.get_data()
    rewrited_question = data['rewrited_question']
    randomized_question_list = data['randomized_question_list']
    chat_id = data['chat_id']
    prompt = data['rewrited_question']

    randomized_question_list.pop(0)

    callback.message.delete_reply_markup()

    if score:
        sqlite3_connector.add_scored_question(prompt)
        await callback.message.answer(f'Thank you! Question: {rewrited_question["response"]} saved')

    if len(randomized_question_list) == 0: 
        # await schedule_next_quiz(message)
        username = sqlite3_connector.get_user_by_chat_id(chat_id)
        logging.info(f'(username: {username}), (chat_id: {chat_id}): Finishing the quiz')
        await callback.message.answer(f'Quiz finished! Well done! 💪')
        if not get_job(callback.from_user.username):
            await schedule_quiz(bot, callback.from_user.username, chat_id)
        await state.clear()


    else:
        await state.update_data(randomized_question_list = randomized_question_list)
        await send_question(bot, state)
