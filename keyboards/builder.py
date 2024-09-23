from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from callbacks.quiz_callback import ReadyCallbackFactory, QuizCallbackFactory
from callbacks.edit_callback import CancelEditCallbackFactory
from callbacks.score_gpt_callback import GPTScoreCallbackFactory
from callbacks.trial_set_callback import TrialSetCallbackFactory
from messages.messages import READY
import random
from service.question import Question
from database.connector import SQLite3Connector as sql3lite_connector

def quiz_ready_keyboard() -> InlineKeyboardMarkup:
     
     keyboard = InlineKeyboardBuilder()

     keyboard.button(
          text = random.choice(READY),
          callback_data = ReadyCallbackFactory()
     )

     return keyboard.as_markup()

def quiz_answers_keyboard(question: Question) -> InlineKeyboardMarkup:
     
     keyboard = InlineKeyboardBuilder()

     random.shuffle(question.answers)

     for answer in question.answers:
          keyboard.button(
               text = answer.text if question.long_asnwers == False else answer.bullet,
               callback_data = QuizCallbackFactory(
                    right = answer.right,
                    id_ = answer.id_
               )
          )


     if not question.long_asnwers: keyboard.adjust(1)


     return keyboard.as_markup()

def score_gpt_keyboard() -> InlineKeyboardMarkup:
     keyboard = InlineKeyboardBuilder()
     keyboard.button(
          text = 'Подходящий вопрос',
          callback_data = GPTScoreCallbackFactory(score = True)
          )
     keyboard.button(
          text = 'Этот вопрос не подходит',
          callback_data = GPTScoreCallbackFactory(score = False)
          )
     
     return keyboard.as_markup()

def cancel_edit_keyboard() -> InlineKeyboardMarkup:

     keyboard = InlineKeyboardBuilder()
     keyboard.button(
          text = 'Отмена',
          callback_data = CancelEditCallbackFactory()
          )
     
     return keyboard.as_markup()

def trial_set_keyboard() -> InlineKeyboardMarkup:

     keyboard = InlineKeyboardBuilder()

     for set_ in sql3lite_connector.get_sets_by_account(0):

          keyboard.button(
               text = set_[1],     # set name
               callback_data = TrialSetCallbackFactory(
                    set_id = set_[0],   # set id
                    set_name = set_[1]
               )
          )
     
     return keyboard.as_markup()