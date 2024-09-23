# aiogram
from aiogram.filters.callback_data import CallbackData

class CancelEditCallbackFactory(CallbackData, prefix = 'cancel'):
    pass