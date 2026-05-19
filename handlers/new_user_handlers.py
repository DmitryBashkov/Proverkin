# aiogram
from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

# project
from service.user import User
from service.quiz import schedule_quiz
from states.states import QuizState, TrialSetSelectionState, EditQuestionsState
from messages.messages import *
from keyboards.builder import trial_set_keyboard
from callbacks.trial_set_callback import TrialSetCallbackFactory

# misc
import logging
from os import linesep
import pickle


# Initialize the module-level router
router: Router = Router()

# Initialize the logger
logger = logging.getLogger(__name__)
linesep = linesep + '- '


@router.message(CommandStart(), ~StateFilter(QuizState.get_answer, QuizState.get_ready, EditQuestionsState.get_updated_file))
async def cmd_start(message: Message, bot: Bot, state: FSMContext, is_test = False):
    user = User(
         username = message.from_user.username, 
         chat_id = message.from_user.id
         )

    logger.info(f'(username: {user.telegram_username}), (chat_id: {user.chat_id}): command /start')


    if not user.exist:
        logger.info(f'(username: {user.telegram_username}), (chat_id: {user.chat_id}): User not found in the database')

        logger.info(f'(username: {user.telegram_username}), (chat_id: {user.chat_id}): Creating a new user')
        user.account_id(0) # trial account
        user.set_default()
        user.create()

        logger.info(f'(username: {user.telegram_username}), (chat_id: {user.chat_id}): Proceeding to trial set selection')
        
        await message.answer(
             text = 'Choose a question list for the trial period', 
             reply_markup = trial_set_keyboard()
        )

        await state.update_data(chat_id = user.chat_id)
        await state.update_data(username = user.telegram_username)

        await state.set_state(TrialSetSelectionState.get_set)

        return

    '''
    If the user was found in the database but has no chat_id, they have never written to the bot.
    We save their chat_id and immediately schedule a quiz.
    '''

    if not user.started:
            logger.info(f'(username: {user.telegram_username}): User has no chat_id')
            await message.answer(MESSAGES['welcome_message'])

            user.add_chat_id()

            logger.info(f'(username: {user.telegram_username}), (chat_id: {user.chat_id}): added chat_id')
            await schedule_quiz(bot, user.telegram_username, user.chat_id)
            return

    # Check if there is a scheduled quiz for the user

    if user.has_job:
        await message.answer('You already have a scheduled quiz at: '
                            f'<b>{user.existing_job.next_run_time.strftime("%d.%m at %H:%M")}</b>',
                            parse_mode = 'HTML')
        return
    
    elif user.active:
        await schedule_quiz(bot, user.username, user.chat_id)

@router.callback_query(TrialSetCallbackFactory.filter(), StateFilter(TrialSetSelectionState.get_set))
async def get_trial_set(callback: CallbackQuery, bot: Bot, state: FSMContext, callback_data = TrialSetCallbackFactory):

    await callback.message.answer(
         f'<b>{callback_data.set_name}/<b> -- great choice!')

    data = await state.get_data()

    user = User(
         username = data['username'],
         chat_id = data['chat_id']
    )

    if callback_data.set_id not in user.sets:
        user.add_set(callback_data.set_id)
    else:
        await callback.message.answer(f'You already have this question set\nPress /quiz to start the quiz')

    await schedule_quiz(bot, user.telegram_username, user.chat_id)
