# aiogram
from aiogram.filters.callback_data import CallbackData

class SelectCallbackFactory(CallbackData, prefix = 'new_user_selection'):
    selection: int
