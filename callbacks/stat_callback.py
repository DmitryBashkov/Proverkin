from aiogram.filters.callback_data import CallbackData

class StatCallbackFactory(CallbackData, prefix = 'stat'):
    mode: str
    user: str
