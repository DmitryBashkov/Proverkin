# project
from database.connector import SQLite3Connector as sqlite3_connector

from utils.misc import get_job

# misc
import logging
import json

logger = logging.getLogger(__name__)

class User:

    '''
    This class represents a telegram user
    '''

    def __init__(self, username = None, chat_id = None, params = ['user_id', 'chat_id'], dump = None):
        

        
        self._telegram_username = username
        self._chat_id = chat_id
        self._active = None

        self._user_id = None
        self._real_name = None
        self._phone_number = None
        self._email = None
        self._timezone = None
        self._quiz_start_hour = None
        self._quiz_end_hour = None
        self._reg_date = None
        self._last_activity = None
        self._user_type = None
        self._account_id = None
        self._is_active = None
        self._has_job = None
        self._existing_job = None
        self._has_quiz = None
        self._sets = None
        self._started = None
        self._exist = None
        self._blocked = None                # заблокирован ли бот пользователем
        

        # getting data from DB and associate it with class attributes
        # e.g. we need to know 'real_name'. We put it into list ['real_name']
        # and the we got attr user._real_name
        if params:
            self._started = False
            data = sqlite3_connector.get_user(
                username = username if username != None else None,
                chat_id = chat_id if chat_id != None else None,
                # params = ['user_id'].append(params) 
                params = params
            )
            if data == None:
                self._exist = False
                return
            
            for i, data_ in enumerate(data):
                if params[i] == 'chat_id':
                    if data_ != None:
                        self._started = True
                    else:
                        continue
                self.__setattr__("_"+params[i], data_)

            if hasattr(self, '_user_id') and self._user_id != None:
                self._exist = True
        
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)

                
    @property
    def sets(self):
        if self._sets is None or self._sets == []:
            self._sets = self._get_user_sets()
        return self._sets
    
    @property
    def user_id(self):
        if self._user_id is None:
            self._user_id = self._get_user_id_from_db()
        return self._user_id
    
    @property
    def exist(self):
        return self._exist
    
    @property
    def telegram_username(self):
        if self._telegram_username is None:
            self._telegram_username = self._get_username_from_db()
        return self._telegram_username
    
    @property
    def chat_id(self):
        if self._chat_id is None:
            self._chat_id = self._get_chat_id_from_db()
        return self._chat_id
    
    @property
    def has_job(self):
        return False if self.existing_job == None else True
    
    @property
    def existing_job(self):
        if self._existing_job is None:
            self._existing_job = get_job(self.telegram_username)
        return self._existing_job
    
    @property
    def active(self):
        return self._active
        
    @property
    def started(self):
        return self._started

    
    def __eq__(self, other):
        return self.username == other.username
    
    def _get_user_sets(self):
        # set_[1] -- set name
        return [set_[1] for set_ in sqlite3_connector.get_users_set_list(self.chat_id)]
    
    def create(
            self,

        ):
        '''
        adding new user into DB: 
            username,
            chat_id,
            account_id,
            user_type,
            active
        returns user_id
        '''

        return sqlite3_connector.add_user(
            telegram_username = self._telegram_username,
            chat_id = self._chat_id,
            real_name = self._real_name,
            account_id = self._account_id,
            user_type = self._user_type,
            active = self._active
            )

    def add_chat_id(self, chat_id: int = None):
        '''
        adding chat_id into DB for user by <self._telegram_username>
        if <chat_id> param is None, adding self._chat_id
        '''
        return sqlite3_connector.add_chat_id(
            self._telegram_username, 
            self.chat_id if chat_id == None else chat_id
            )
    
    def set_default(self):
        self._active = 1
        self._user_type = 'user'
    
    def add_set(self, set_id: int):
        '''
        adding set_id for user
        '''
        return sqlite3_connector.add_set(
            user_id = self.user_id,
            set_id = set_id,
            qty = 3
            )
    
    def uprint(self):
        '''
        return string with basic user data: username, chat_id, user_id
        this func need for logging
        '''
        return f"username: {self._telegram_username} | chat_id: {self._chat_id} | user_id: {self._user_id}"
    
    def _get_chat_id(self):
        return sqlite3_connector.get_user_by_chat_id()
    
    @property
    def account_id(self):
        return self._account_id

    @account_id.setter
    def account_id(self, account_id: int):
        self._account_id = account_id


    
    
      


    
    
    # class User:
    #     def __init__(self, user_id):
    #         self.user_id = user_id
    #         self._name = None
    #         self._email = None
    #         self._age = None
    #         # Другие атрибуты...

    #     @property
    #     def name(self):
    #         if self._name is None:
    #             self._name = self._get_name_from_db()
    #         return self._name

    #     @property
    #     def email(self):
    #         if self._email is None:
    #             self._email = self._get_email_from_db()
    #         return self._email

    #     @property
    #     def age(self):
    #         if self._age is None:
    #             self._age = self._get_age_from_db()
    #         return self._age

    #     # Другие методы доступа к атрибутам...

    #     def _get_name_from_db(self):
    #         # Логика получения значения атрибута name из БД
    #         return "John Doe"

    #     def _get_email_from_db(self):
    #         # Логика получения значения атрибута email из БД
    #         return "johndoe@example.com"

    #     def _get_age_from_db(self):
    #         # Логика получения значения атрибута age из БД
    #         return 30
