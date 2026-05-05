# project
from utils.schedulers import quiz_scheduler
from utils.state import state_store
from utils.bot_client import bot_client
from utils.misc import get_new_time, get_job
from database.connector import PostgresConnector as pg
from service.question import Question, get_randomized_question_list
from service.keyboards import quiz_ready_keyboard, quiz_answers_keyboard
from service import messages as msgs

# misc
import logging
import random
import datetime
import time
import asyncio

logger = logging.getLogger(__name__)

# для маркированного списка
_LINESEP = '\n- '


# ====== планирование ======

async def schedule_quiz(username: str, chat_id: int, notify: bool = True) -> None:
    run_date = get_new_time()
    quiz_scheduler.add_job(check_for_quiz,
                           'date',
                           [chat_id],
                           run_date = run_date,
                           name = f'{username}')

    logger.info(f'(username: {username}), (chat_id: {chat_id}): '
                f'квиз запланирован на {run_date.strftime("%d.%m в %H:%M")}')

    if notify:
        await bot_client.send_message(
            chat_id = chat_id,
            text = f'Следующий квиз запланирован на <b>{run_date.strftime("%d.%m в %H:%M")}</b>'
        )


# ====== старт квиза ======

async def check_for_quiz(chat_id: int) -> None:

    if not pg.user_has_sets(chat_id):
        username = pg.get_user_by_chat_id(chat_id)
        logger.info(f'(username: {username}), (chat_id: {chat_id}): '
                    'для пользователя не назначено вопросов')
        await bot_client.send_message(chat_id, 'Для тебя пока не назначено вопросов')
        await schedule_quiz(username = username, chat_id = chat_id, notify = True)
        return

    sets_list = pg.get_users_set_list(chat_id = chat_id)

    msg_text = []
    for _set in sets_list:
        msg_text.append(f'{_set[1]}: {_set[2]} вопросов')

    await bot_client.send_message(
        chat_id = chat_id,
        text = f'Готов?\n\nДля тебя есть вопросы из списков:\n\n- '
               + _LINESEP.join(msg_text),
        reply_markup = quiz_ready_keyboard()
    )

    await state_store.update_data(chat_id, chat_id = chat_id)
    await state_store.set_state(chat_id, 'get_ready')


async def start_quiz(chat_id: int) -> None:

    randomized_question_list = get_randomized_question_list(chat_id)
    all_questions_sum = len(randomized_question_list)
    username = pg.get_user_by_chat_id(chat_id)
    logger.info(f'(username: {username}), (chat_id: {chat_id}): '
                f'количество вопросов -- {all_questions_sum}')

    if all_questions_sum == 0:
        await bot_client.send_message(chat_id, 'Для тебя пока не назначено вопросов')
        await state_store.clear(chat_id)
        await schedule_quiz(username = username, chat_id = chat_id)
        return

    await state_store.update_data(
        chat_id,
        randomized_question_list = randomized_question_list,
        all_questions_sum = all_questions_sum
    )

    await send_question(chat_id)


async def send_question(chat_id: int) -> None:
    data = await state_store.get_data(chat_id)
    randomized_question_list = data['randomized_question_list']
    all_questions_sum = data['all_questions_sum']

    question = Question(randomized_question_list[0])
    await state_store.update_data(chat_id, question_id = randomized_question_list[0])

    text = (
        f'❓ Вопрос ({all_questions_sum - len(randomized_question_list) + 1}/{all_questions_sum})\n\n'
        f'<b>{question.text}</b>'
    )

    # отправляем сам вопрос (без клавиатуры)
    sent = await bot_client.send_message(chat_id = chat_id, text = text)
    question_msg_id = sent.get('message_id')

    # сообщение про задержку появления ответов
    delay_sec = max(1, len(question.text) // 30)
    warn = await bot_client.send_message(
        chat_id = chat_id,
        text = f'Ответы появятся через {delay_sec} сек.'
    )
    warn_msg_id = warn.get('message_id')

    await asyncio.sleep(delay_sec)

    # удаляем "ответы появятся через..." и редактируем сам вопрос,
    # добавляя клавиатуру с вариантами
    if warn_msg_id:
        await bot_client.delete_message(chat_id, warn_msg_id)
    if question_msg_id:
        await bot_client.edit_reply_markup(
            chat_id = chat_id,
            message_id = question_msg_id,
            reply_markup = quiz_answers_keyboard(question)
        )

    await state_store.update_data(chat_id, start_time = time.time())
    await state_store.set_state(chat_id, 'get_answer')


# ====== обработка нажатий ======

async def handle_ready(chat_id: int, message_id: int, callback_id: str) -> None:
    state = await state_store.get(chat_id)
    if state['state'] != 'get_ready':
        await bot_client.answer_callback(callback_id)
        return

    await bot_client.edit_reply_markup(chat_id, message_id, reply_markup = None)
    await bot_client.answer_callback(callback_id)
    await start_quiz(chat_id)


async def handle_answer(chat_id: int, message_id: int, callback_id: str,
                        username: str, payload: dict) -> None:
    end_time = time.time()

    state = await state_store.get(chat_id)
    if state['state'] != 'get_answer':
        await bot_client.answer_callback(callback_id)
        return

    data = state['data']
    question_id = int(data.get('question_id') or payload.get('q'))
    start_time = data.get('start_time', end_time)

    is_right = bool(int(payload.get('r', 0)))
    answer_id = int(payload.get('a', 0))
    incorrect_question = bool(int(payload.get('bad', 0)))

    answer_text = None

    if incorrect_question:
        await bot_client.send_message(chat_id, 'Спасибо, информацию зафиксировали!')
        pg.update_question_type(int(payload.get('q', question_id)), 'incorrect')
        await bot_client.answer_callback(callback_id)
    else:
        rows = pg.get_answers(answer_id = answer_id)
        answer_text = rows[0][0] if rows else ''

        if is_right:
            await bot_client.answer_callback(
                callback_id, text = '✅ ' + random.choice(msgs.CONGRATS), show_alert = True
            )
            await bot_client.send_message(chat_id, f'✅ {answer_text}')
        else:
            await bot_client.answer_callback(
                callback_id, text = '❌ ' + random.choice(msgs.WRONG), show_alert = True
            )
            await bot_client.send_message(chat_id, f'❌ {answer_text}')
            right_rows = pg.get_answers(question_id = question_id, right = True)
            if right_rows:
                await bot_client.send_message(
                    chat_id, f'Правильный ответ: {right_rows[0][0]}'
                )

        await bot_client.edit_reply_markup(chat_id, message_id, reply_markup = None)

    # логируем результат
    pg.add_log([
        datetime.date.today().isoformat(),
        *pg.get_log_data(question_id, chat_id),
        int(is_right),
        answer_text,
        end_time - start_time
    ])

    # двигаемся к следующему вопросу
    randomized_question_list = data['randomized_question_list']
    randomized_question_list.pop(0)

    if len(randomized_question_list) == 0:
        logger.info(f'(username: {username}), (chat_id: {chat_id}): заканчиваем квиз')
        await bot_client.send_message(chat_id, 'Квиз закончен! Молодец! 💪')
        if not get_job(username):
            await schedule_quiz(username, chat_id)
        await state_store.clear(chat_id)
    else:
        await state_store.update_data(chat_id, randomized_question_list = randomized_question_list)
        await send_question(chat_id)


# ====== восстановление расписания после перезапуска ======

async def reschedule_all_active_users() -> int:
    total = 0
    for username, chat_id in pg.get_all_active_users_with_chat_id():
        await schedule_quiz(username, chat_id, notify = False)
        total += 1
    return total
