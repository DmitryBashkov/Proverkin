from aiogram.filters.state import StatesGroup, State

class QuizState(StatesGroup):
    get_ready = State()
    get_answer = State()

class CreateTableState(StatesGroup):
    get_table_link = State()

class EditQuestionsState(StatesGroup):
    get_updated_file = State ()

class TrialSetSelectionState(StatesGroup):
    get_set = State()

