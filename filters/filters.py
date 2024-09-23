from aiogram.filters import BaseFilter
from aiogram.types import Message
from database.connector import SQLite3Connector as sqlite3_connector
import pathlib


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return sqlite3_connector.is_admin(message.from_user.id)
    

class IsExist(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return sqlite3_connector.is_exist(message.from_user.id) == True
    
class IsDocument(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.content_type == 'document':
            ext = pathlib.Path(message.document.file_name).suffix
            if  ext in {'.xls', '.xlsx'}:
                return True
            
            else:
                await message.answer(f'Неверный формат файла {format(pathlib.Path(message.document.file_name).suffix)}')
                return False
        else:
            return False
