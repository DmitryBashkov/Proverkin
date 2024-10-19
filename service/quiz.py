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

# переопределяем linesep, тк нам нужно делать маркированный список
linesep = '\n- '


async def schedule_quiz(bot: Bot, username: str, chat_id: int, notify_user: bool = True) -> None:
    run_date = get_new_time()
    quiz_scheduler.add_job(check_for_quiz, 
                           'date', 
                           [bot, chat_id], 
                           run_date = run_date, 
                           name = f'{username}')
    
    logger.info(f'(username: {username}), (chat_id: {chat_id}): Квиз для запланирован на {run_date.strftime("%d.%m в %H:%M")}')

    if notify_user:
        try:
            await bot.send_message(chat_id = chat_id,
                                text = f'Следующий квиз запланирован на <b>{run_date.strftime("%d.%m в %H:%M")}</b>',
                                parse_mode = 'HTML')
        except TelegramForbiddenError as e:
            logging.error(f'(username: {username}), (chat_id: {chat_id}): {e}')

async def check_for_quiz(bot: Bot, chat_id: int) -> None:

    if not sqlite3_connector.user_has_sets(chat_id):
        username = sqlite3_connector.get_user_by_chat_id(chat_id)
        logger.info(f'(username: {username}), (chat_id: {chat_id}): для пользователя не назначено вопросов')
        await bot.send_message(chat_id, 'Для тебя пока не назначено вопросов')
        await schedule_quiz(bot, username = username, chat_id = chat_id, notify_user = True)
        return

    state: FSMContext = FSMContext(dp.storage, StorageKey(bot.id, chat_id, chat_id))

    sets_list = sqlite3_connector.get_users_set_list(chat_id = chat_id)

    msg_text = []

    for _set in sets_list:
        msg_text.append(f'{_set[1]}: {_set[2]} вопросов')
    
    try:
        await bot.send_message(
            chat_id = chat_id, 
            text = f'Готов?\n\nДля тебя есть вопросы из списков:\n\n- {linesep.join(msg_text)}', 
            reply_markup = quiz_ready_keyboard()
        )
    except TelegramForbiddenError as e:
        logging.error(f'(username: {username}), (chat_id: {chat_id}): {e}')
    
    await state.update_data(chat_id = chat_id)

    await state.set_state(QuizState.get_ready)

async def start_quiz(bot: Bot, state: FSMContext) -> None:
    data = await state.get_data()
    chat_id = data['chat_id']

    # получаем список вопросов для пользователя
    randomized_question_list = sqlite3_connector.get_randomized_question_list(chat_id)
    all_questions_sum = len(randomized_question_list)
    username = sqlite3_connector.get_user_by_chat_id(chat_id)
    logger.info(f'(username: {username}), (chat_id: {chat_id}): количество вопросов -- {all_questions_sum}')
    
    # заносим в state список вопросов
    # await state.update_data(randomized_question_list = randomized_question_list)

    # эта перменная нам нужна, чтобы сообщать пользователю, сколько вопросов остается
    # например, вопрос 4/10. переменная хранит число 10 
    await state.update_data(all_questions_sum = all_questions_sum)
    await state.update_data(randomized_question_list = randomized_question_list)

    await send_question(bot, state)

async def send_question(bot: Bot, state: FSMContext) -> None:
    data = await state.get_data()

    randomized_question_list = data['randomized_question_list']
    all_questions_sum = data['all_questions_sum']
    chat_id = data['chat_id']

    test_chat_ids = [
        # '477582303',    # Дима
        '1334370908',   # Наташа
        '494656681'     # Вика
    ]

    # берем первый вопрос в списке (потом мы удаляем этот же первый вопрос)
    question = Question(randomized_question_list[0])
    await state.update_data(question_id = randomized_question_list[0])

    test = False

    if str(chat_id) in test_chat_ids:
        rewrited_question = rewrite(question.text)
        await state.update_data(rewrited_question = rewrited_question)
        rewrited_question_text = f'{rewrited_question["response"]}\n\nОбычный: {question.text}'
        test = True

    # Заводим отдельную переменную для сообщения, 
    # потому что нужно будет потом отредактировать (добавить ответы в виде reply markup)
    question_msg = await bot.send_message(chat_id = chat_id, 
                                          text = f'❓ Вопрос ({all_questions_sum - len(randomized_question_list) + 1}/{all_questions_sum})\n\n'
                                          f'<b>{rewrited_question_text if test else question.text}</b>', 
                                          parse_mode = 'HTML',
                                          reply_markup = None)
    
    '''Cообщение показывает, через сколько времени появятся ответы на вопрос. 
    Это сделано, чтобы пользователи не ориентировались на выпадающие ответы
    Делаем отдеkьную переменную, тк потом нам нужно его удалить ''' 

    warning_msg = await bot.send_message(chat_id = chat_id, 
                                         text = f'Ответы появятся через {len(question.text)//30} сек.')
    
    # ставим паузу перед показом ответов, что бы пользователь сначала прочел вопрос. 
    # Время высчитывается из среднего времени чтения (863 символа в минуту)
    # time.sleep(len(question.text)/30)

    #удаляем и добавляем клавиатуру с ответами
    await warning_msg.delete()
    if str(chat_id) in test_chat_ids:
        await question_msg.edit_reply_markup(reply_markup = score_gpt_keyboard())
    else:
        await question_msg.edit_reply_markup(reply_markup = quiz_answers_keyboard(question))

    # удаляем первый в списке вопрос (мы его только что задали)

    # переходим в ожидание ответа от пользователя
    await state.update_data(start_time = time.time())
    await state.set_state(QuizState.get_answer)


    