# aiogram
from aiogram.filters.callback_data import CallbackData

class QuizCallbackFactory(CallbackData, prefix = 'quiz'):
    right: bool
    id_: int
    incorrect_question: bool
    question_id: int


class ReadyCallbackFactory(CallbackData, prefix = 'ready'):
    pass