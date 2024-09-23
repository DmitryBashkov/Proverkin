# aiogram
from aiogram.filters.callback_data import CallbackData

class TrialSetCallbackFactory(CallbackData, prefix = 'trial_set'):
    set_id: int
    set_name: str