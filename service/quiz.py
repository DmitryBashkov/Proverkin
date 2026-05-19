# aiogram
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.exceptions import TelegramForbiddenError

# project
from utils.schedulers import quiz_scheduler
from service.question import Question
from states.states import QuizState
from utils.misc import get_new_time
from utils.bot_dispatcher import dp
from database.connector import SQLite3Connector as sqlite3_connector
from keyboards.builder import quiz_ready_keyboard, quiz_answers_keyboard, score_gpt_keyboard
from utils.gtp_rewriter import rewrite


# misc
import logging
from os import linesep
import time



logger = logging.getLogger(__name__)

# Redefine linesep since we need to build a bulleted list
linesep = '\n- '


async def schedule_quiz(bot: Bot, username: str, chat_id: int, notify: bool = True) -> None:
    run_date = get_new_time()
    quiz_scheduler.add_job(check_for_quiz, 
                           'date', 
                           [bot, chat_id], 
                           run_date = run_date, 
                           name = f'{username}')
    
    logger.info(f'(username: {username}), (chat_id: {chat_id}): Quiz scheduled for {run_date.strftime("%d.%m at %H:%M")}')

    if notify:
        try:
            await bot.send_message(chat_id = chat_id,
                                text = f'Next quiz scheduled for <b>{run_date.strftime("%d.%m at %H:%M")}</b>',
                                parse_mode = 'HTML')
        except TelegramForbiddenError as e:
            logging.error(f'(username: {username}), (chat_id: {chat_id}): {e}')

async def check_for_quiz(bot: Bot, chat_id: int) -> None:

    if not sqlite3_connector.user_has_sets(chat_id):
        username = sqlite3_connector.get_user_by_chat_id(chat_id)
        logger.info(f'(username: {username}), (chat_id: {chat_id}): no questions assigned for the user')
        await bot.send_message(chat_id, 'No questions have been assigned for you yet')
        await schedule_quiz(bot, username = username, chat_id = chat_id, notify = True)
        return

    state: FSMContext = FSMContext(dp.storage, StorageKey(bot.id, chat_id, chat_id))

    sets_list = sqlite3_connector.get_users_set_list(chat_id = chat_id)

    msg_text = []

    for _set in sets_list:
        msg_text.append(f'{_set[1]}: {_set[2]} questions')
    
    try:
        await bot.send_message(
            chat_id = chat_id, 
            text = f'Ready?\n\nYou have questions from the following lists:\n\n- {linesep.join(msg_text)}', 
            reply_markup = quiz_ready_keyboard()
        )
    except TelegramForbiddenError as e:
        logging.error(f'(username: {username}), (chat_id: {chat_id}): {e}')
    
    await state.update_data(chat_id = chat_id)

    await state.set_state(QuizState.get_ready)

async def start_quiz(bot: Bot, state: FSMContext) -> None:
    data = await state.get_data()
    chat_id = data['chat_id']

    # Get the question list for the user
    randomized_question_list = sqlite3_connector.get_randomized_question_list(chat_id)
    all_questions_sum = len(randomized_question_list)
    username = sqlite3_connector.get_user_by_chat_id(chat_id)
    logger.info(f'(username: {username}), (chat_id: {chat_id}): number of questions -- {all_questions_sum}')
    
    # Store the question list in state
    # await state.update_data(randomized_question_list = randomized_question_list)

    # This variable is used to inform the user how many questions remain,
    # e.g. question 4/10. It stores the number 10.
    await state.update_data(all_questions_sum = all_questions_sum)
    await state.update_data(randomized_question_list = randomized_question_list)

    await send_question(bot, state)

async def send_question(bot: Bot, state: FSMContext) -> None:
    data = await state.get_data()

    randomized_question_list = data['randomized_question_list']
    all_questions_sum = data['all_questions_sum']
    chat_id = data['chat_id']

    test_chat_ids = [
        # '477582303',    # Dima
        # '1334370908',   # Natasha
        # '494656681'     # Vika
    ]

    # Take the first question in the list (we will delete this same first question later)
    question = Question(randomized_question_list[0])
    await state.update_data(question_id = randomized_question_list[0])

    test = False

    if str(chat_id) in test_chat_ids:
        rewrited_question = rewrite(question.text)
        await state.update_data(rewrited_question = rewrited_question)
        rewrited_question_text = f'{rewrited_question["response"]}\n\nOriginal: {question.text}'
        test = True

    # Create a separate variable for the message
    # because we will need to edit it later (to add answers as a reply markup)
    question_msg = await bot.send_message(chat_id = chat_id, 
                                          text = f'❓ Question ({all_questions_sum - len(randomized_question_list) + 1}/{all_questions_sum})\n\n'
                                          f'<b>{rewrited_question_text if test else question.text}</b>', 
                                          parse_mode = 'HTML',
                                          reply_markup = None)
    
    '''A message showing how many seconds until the answers appear.
    This is done so that users do not rely on the answer buttons appearing.
    We use a separate variable since we need to delete it later.''' 

    warning_msg = await bot.send_message(chat_id = chat_id, 
                                         text = f'Answers will appear in {len(question.text)//30} sec.')
    
    # Pause before showing answers so the user reads the question first.
    # Time is calculated from average reading speed (863 characters per minute).
    # time.sleep(len(question.text)/30)

    # Delete and re-add the keyboard with answers
    await warning_msg.delete()
    if str(chat_id) in test_chat_ids:
        await question_msg.edit_reply_markup(reply_markup = score_gpt_keyboard())
    else:
        await question_msg.edit_reply_markup(reply_markup = quiz_answers_keyboard(question))

    # Delete the first question from the list (we just asked it)

    # Wait for the answer from the user
    await state.update_data(start_time = time.time())
    await state.set_state(QuizState.get_answer)
