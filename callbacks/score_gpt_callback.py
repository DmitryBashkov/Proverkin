# aiogram
from aiogram.filters.callback_data import CallbackData

class GPTScoreCallbackFactory(CallbackData, prefix = 'gpt_score'):
    score: bool