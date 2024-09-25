import logging
import sqlite3
from typing import Any, Literal
from config_data.config import config
import random
import os
from mysql.connector import connect, Error
import json

logger = logging.getLogger(__name__)

class MySQLConnector:

    @staticmethod
    def execute(sql_request: str,
                request_type: Literal['fetchall', 'fetchone', 'commit'],
                iterator = False,
                args = ()):
        
        try:
            with connect(
                host = config.db.r_host,
                user = config.db.r_user,
                password = config.db.r_password,
                database = config.db.r_database

            ) as db_connection:
                db_cursor = db_connection.cursor()

                match request_type:
                    case 'fetchall':
                        if iterator: 
                            return db_cursor.execute(sql_request, args).fetchall()
                        else:
                            return db_cursor.execute(sql_request, args).fetchall()
                    
                    case 'fetchone':
                        return db_cursor.execute(sql_request, args).fetchone()
                    
                    case 'commit':
                        db_cursor.execute(sql_request, args)
                        db_connection.commit()
                        
        except sqlite3.Error as error:
            logging.info(f'''MySQL execution error:\n
                        Error: {error}\n
                        SQL request: {sql_request}\n
                        Request type: {request_type}''')

        finally:
            if(db_connection):
                db_connection.close()
    
    def add_log(log) -> None:
        query = \
            '''
            INSERT INTO logs (quiz_date, account_id, user_id, real_name, telegram_username, set_id, set_name, question_id, question_text, result, answer_text, answer_time) 
			VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            '''

        MySQLConnector.execute(
            query,
            'commit',
            False,
            log
        )

        # try:
        #     db_connection = sqlite3.connect(database_path)
        #     db_cursor = db_connection.cursor()

        #     match request_type:
        #         case 'fetchall':
        #             if iterator: 
        #                 return db_cursor.execute(sql_request, args).fetchall()
        #             else:
        #                 return db_cursor.execute(sql_request, args).fetchall()
                
        #         case 'fetchone':
        #             return db_cursor.execute(sql_request, args).fetchone()
                
        #         case 'commit':
        #             db_cursor.execute(sql_request, args)
        #             db_connection.commit()

        # except sqlite3.Error as error:
        #     logging.info(f'''{database_path} execution error:\n
        #                 Error: {error}\n
        #                 SQL request: {sql_request}\n
        #                 Request type: {request_type}''')

        # finally:
        #     if(db_connection):
        #         db_connection.close()

class SQLite3Connector:

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SQLite3Connector, cls).__new__(cls)
        return cls.instance

    @staticmethod
    def add_user(
        telegram_username: str = None,
        chat_id: str = None,
        real_name: str = None,
        # phone_number: str = None,
        # timezone: str = None,
        # quiz_start_hour: str = None,
        # quiz_end_hour: str = None,
        # last_activity: str = None,
        user_type: str = 'user',
        account_id: int = None,
        active: int = 1 
    ) -> int:
        
        query = \
        '''
        insert into 
            users 
        (
            telegram_username,
            chat_id,
            real_name,
            user_type,
            account_id,
            active
        )
        values
            (?,?,?,?,?,?)
        returning 
            user_id
        '''
        user_id = SQLite3Connector.execute(config.db.l_path,
                          query,
                          request_type = 'returning',
                          args = (telegram_username, chat_id, real_name, user_type, account_id, active))[0]
        return user_id
        
    @staticmethod
    def add_set(user_id, set_id: int, qty: int = 3):
        '''
        adding set_id for a user
        '''

        query = \
        '''
        insert into 
            user_sets
        (user_id, set_id, qty)
        values (?,?,?)
        '''

        return SQLite3Connector.execute(
            config.db.l_path,
            query,
            request_type = 'commit',
            args = (user_id, set_id, qty)
            )

    @staticmethod
    def update_user(user_id: int, telegram_username: str, real_name: str, active: int):
        query = \
        '''
        update users
        set telegram_username = ?, real_name = ?, active = ?
        where
        user_id = ?
        '''
        SQLite3Connector.execute(config.db.l_path,
                          query,
                          request_type = 'commit',
                          args = (telegram_username, real_name, active, user_id))
        
    @staticmethod
    def set_set_qty(user_id: int, set_id: int, qty: int): 

        add_qty_query = \
        '''
        insert into user_sets
        (user_id, set_id, qty)
        values
        (?,?,?)
        '''
        
        update_qty_query = \
        '''
        update user_sets
        set qty = ?
        where
        user_id = ? and set_id = ?
        '''

        remove_qty_record_query = \
        '''
        delete from user_sets
        where
        user_id = ? and set_id = ?
        '''

        # создаем массив с  set_id, которые есть у пользователя
        set_list = SQLite3Connector.get_users_set_list(user_id = user_id)
        user_sets = [set_[0] for set_ in set_list]
        
        # если сета, в который нужно внести изменения нет в списке, 
        # то мы либо ничего не делаем, либо удаляем запись
        # если есть, то апдейтим запись

        # zero_qty = qty == 0 | type(qty) == None or qty == '0' or qty == ' ' or qty == None

        if set_id not in user_sets:

            if qty == 0 or type(qty) == None or qty == '0' or qty == None or qty == ' ':
                return
            else:
                SQLite3Connector.execute(config.db.l_path,
                                         add_qty_query,
                                         request_type = 'commit',
                                         args = (user_id, set_id, qty))
        else:
            if qty == 0 or type(qty) == None or qty == '0' or qty == None or qty == ' ':
                SQLite3Connector.execute(config.db.l_path,
                                         remove_qty_record_query,
                                         request_type = 'commit',
                                         args = (user_id, set_id))
            else:
                SQLite3Connector.execute(config.db.l_path,
                                        update_qty_query,
                                        request_type = 'commit',
                                        args = (qty, user_id, set_id))

                


        # во всех остальных случая обновляем количество вопросов
    
    @staticmethod
    def execute(database_path: str,
                sql_request: str,
                request_type: Literal['fetchall', 'fetchone', 'commit', 'returning'],
                iterator = False,
                args = ()) -> Any:
        
        result = None

        try:
            db_connection = sqlite3.connect(database_path)
            db_cursor = db_connection.cursor()

            match request_type:
                case 'fetchall':
                    if iterator: 
                        result = db_cursor.execute(sql_request, args).fetchall()
                    else:
                        result = db_cursor.execute(sql_request, args).fetchall()
                
                case 'fetchone':
                    result = db_cursor.execute(sql_request, args).fetchone()
                
                case 'commit':
                    result = db_cursor.execute(sql_request, args)
                    db_connection.commit()

                case 'returning':
                    result = db_cursor.execute(sql_request, args).fetchone()
                    
                    
                    

        except sqlite3.Error as error:
            print(error)
            logger.info(f'''{database_path} execution error:\n
                        Error: {error}\n
                        SQL request: {sql_request}\n
                        Request type: {request_type}''')

        finally:
            if(db_connection):
                if (request_type == 'returning'):
                    db_connection.commit()
                    db_connection.close()
        
        return result

    @staticmethod
    def init_check() -> bool:

        if os.path.exists(config.db.l_path):

            command = \
                """
                SELECT name
                FROM sqlite_master 
                WHERE type='table'
                """
            
            table_set = set(row[0] for row in SQLite3Connector.execute(config.db.l_path,
                                        command,
                                        request_type = 'fetchall'))
            
            if {'users',  
                'accounts', 
                'sets', 
                'questions', 
                'answers',
                'user_sets', 
                'logs'}.issubset(table_set):
                
                return True
            else:
                print(f'Проверьте базу данных. Список таблиц: {table_set}')
                return False
            
        else:
            logging.info(f'Отсутствует файл базы данных: {config.db.l_path}')
               
    @staticmethod
    def is_admin(chat_id):

        '''
        returns str value of the column user_type ('admin' or 'user')
        '''
        request = \
        '''
        select user_type
        from users
        where chat_id = ?
        '''

        
        record = SQLite3Connector.execute(config.db.l_path,
                                 request,
                                 request_type = 'fetchone',
                                 args = (chat_id,))
        
        if record == None: 
            return False
        else:
            return record[0] == 'admin' 
        
    @staticmethod
    def is_exist(chat_id):
        request = \
        '''
        select user_id
        from users
        where chat_id = ?
        '''

        
        record = SQLite3Connector.execute(config.db.l_path,
                                 request,
                                 request_type = 'fetchone',
                                 args = (chat_id,))
        
        return record != None

    @staticmethod
    def get_account_name(account_id):
        request = \
        '''
        select account_name
        from accounts
        where account_id = ?
        '''

        return SQLite3Connector.execute(config.db.l_path,
                                 request,
                                 request_type = 'fetchone',
                                 args = (account_id,))[0]

    @staticmethod
    def get_account_id_by_chat_id(chat_id: int):
        '''
        Возвращает account_id по chat_id
        '''
        request = \
        '''
        select account_id
        from users
        where chat_id = ?
        '''

        return SQLite3Connector.execute(config.db.l_path,
                                 request,
                                 request_type = 'fetchone',
                                 args = (chat_id,))[0]
        
    @staticmethod
    def get_user(chat_id = None, username = None, params = None):

        '''
        returns (telegram_username, chat_id, *params)
        use params to define exactly what you need
        '''

        if params == None:
            return None
        
        result = None
        request = \
        f'''
        select
            {",".join(params)}
        from 
            users
        where
        '''

        if chat_id != None:
            result = SQLite3Connector.execute(config.db.l_path,
                                    request + "chat_id = ?",
                                    request_type = 'fetchone',
                                    args = (chat_id,))
        
        if result != None: 
            return result
        else:
            result = SQLite3Connector.execute(config.db.l_path,
                                    request + "telegram_username = ?",
                                    request_type = 'fetchone',
                                    args = (username,))
        
        return result
        

    @staticmethod
    def get_all_users_by_account_id(account_id: int) -> list:
        '''
        returns (user_id, telegram_username, real_name, active)
        '''

        request = \
        '''
        select user_id, telegram_username, real_name, active
        from users
        where account_id = ?
        '''

        return SQLite3Connector.execute(config.db.l_path,
                                 request,
                                 request_type = 'fetchall',
                                 args = (account_id,))

    @staticmethod
    def get_user_by_chat_id(chat_id):
        '''
        returns username by chat_id
        '''
        command = \
        '''
        select telegram_username
        from users
        where chat_id = ?
        '''

        return SQLite3Connector.execute(config.db.l_path,
                                 command,
                                 request_type = 'fetchone',
                                 args = (chat_id,))[0]

    @staticmethod
    def add_chat_id(username: str, chat_id: int):

        '''
        sets "chat_id" for user with "username" 
        '''

        query = \
        '''
        UPDATE users 
        SET chat_id = ? 
        WHERE telegram_username = ?
        '''

        return SQLite3Connector.execute(config.db.l_path,
                          query,
                          request_type = 'commit',
                          args = (chat_id, username))
    
    @staticmethod
    def set_user_active(username: str,
                        active: int) -> None:
        command = \
        '''
        UPDATE users 
        SET active = ? 
        WHERE username = ?
        '''

        SQLite3Connector.execute('database/users',
                          command,
                          request_type = 'commit',
                          args = (active, username))

    @staticmethod
    def set_user_status(username: str,
                        status: Literal['admin', 'user']) -> None:
        command = \
        '''
        UPDATE users 
        SET status = ? 
        WHERE username = ?
        '''

        SQLite3Connector.execute('database/users',
                          command,
                          request_type = 'commit',
                          args = (status, username))

    @staticmethod
    def add_scored_question(prompt: str) -> None:
        
        query = \
        '''
        INSERT INTO scored_questions 
        (prompt)
        VALUES (?)
        '''

        SQLite3Connector.execute(
            config.db.l_path,
            query,
            'commit',
            False,
            (json.dumps(prompt, ensure_ascii=False),)
        )

    @staticmethod
    def get_user_qty() -> int:
        query = \
        '''
        SELECT user_id
        FROM users 
        '''

        return len(SQLite3Connector.execute(config.db.l_path,
                                 query,
                                 request_type = 'fetchall'))
    
    @staticmethod
    def get_all_active_users_with_chat_id() -> list:

        query = \
        '''
        SELECT telegram_username, chat_id
        FROM users 
        WHERE chat_id IS NOT NULL AND active = 1
        '''
        
        return SQLite3Connector.execute(config.db.l_path,
                          query,
                          request_type = 'fetchall',
                          iterator = True)
    
    @staticmethod
    def get_answers(question_id: int = None, answer_id: int = None, right: bool = None) -> list:
        
        if question_id == None:
            if answer_id == None: return ''

            query = \
            '''
            select text from answers where answer_id = ? order by right desc;
            '''

            result = SQLite3Connector.execute(
                config.db.l_path,
                query,
                'fetchall',
                False,
                (answer_id,)
            )

            return result # [row[0] for row in result]
        
        else:
            if right != None:
                query = \
                '''
                select text from answers where question_id = ? and right = ?;
                '''

                return SQLite3Connector.execute(
                    config.db.l_path,
                    query,
                    'fetchall',
                    False,
                    (question_id, right)
                )
            else:
                query = \
                '''
                select answer_id, text, right from answers where question_id = ?;
                '''

                return SQLite3Connector.execute(
                    config.db.l_path,
                    query,
                    'fetchall',
                    False,
                    (question_id,)
                )
    
    @staticmethod
    def get_users_set_list(chat_id: int = None, user_id: int = None) -> list:
        
        '''
        returns (set_id, set_name, qty) for user by chat_id or user_id
        '''
        query = \
        f'''
        select sets.set_id, sets.set_name, user_sets.qty from users
        join sets on sets.set_id = user_sets.set_id
        join user_sets on user_sets.user_id = users.user_id
        where {'users.chat_id' if chat_id != None else 'users.user_id'} = ?;

        '''

        result = SQLite3Connector.execute(
            config.db.l_path,
            query,
            'fetchall',
            False,
            (chat_id if chat_id != None else user_id,)
        )

        return result # [row[0] for row in result]
    
    @staticmethod
    def get_randomized_question_list(chat_id):
        
        sets_list = SQLite3Connector.get_users_set_list(chat_id)
        question_list = []

        for _set in sets_list:
            questions = SQLite3Connector.get_question_ids_by_set_id(_set[0])
            random.shuffle(questions)

            question_list.extend(questions[:_set[2]])
                
        return question_list

    @staticmethod
    def get_question_ids_by_set_id(set_id) -> list:
        
        
        query = \
        '''
        select question_id from questions where set_id = ?;
        '''

        result = SQLite3Connector.execute(
            config.db.l_path,
            query,
            'fetchall',
            False,
            (set_id,)
        )

        return [row[0] for row in result]
    
    @staticmethod
    def get_question_text(question_id) -> str:
        
        
        query = \
        '''
        select text from questions where question_id = ?;
        '''

        return SQLite3Connector.execute(
            config.db.l_path,
            query,
            'fetchall',
            False,
            (question_id,)
        )[0][0]
    
    @staticmethod
    def get_log_data(question_id, chat_id) -> list:
        
        query = \
        '''
        select account_id, user_id, real_name, telegram_username
        from users 
        where chat_id = ?
        '''

        result = SQLite3Connector.execute(
            config.db.l_path,
            query,
            'fetchall',
            False,
            (chat_id,)
        )

        result = result[0]

        query = \
        '''
        select sets.set_id, sets.set_name, questions.question_id, questions.text 
        from questions
        join sets on sets.set_id = questions.set_id
        where questions.question_id  = ?;
        '''

        return result + SQLite3Connector.execute(
            config.db.l_path,
            query,
            'fetchall',
            False,
            (question_id,)
        )[0]
    
    def user_has_sets(chat_id) -> bool:
        query = \
        '''
        SELECT user_sets.set_id 
        from user_sets
        join users on users.user_id = user_sets.user_id
        where users.chat_id = ?;
        '''

        result = SQLite3Connector.execute(
            config.db.l_path,
            query,
            'fetchall',
            False,
            (chat_id,)
        )


        return len(result) != 0

    def add_log(log) -> None:
        query = \
            '''
            INSERT INTO logs (quiz_date, account_id, user_id, real_name, telegram_username, set_id, set_name, question_id, question_text, result, answer_text, answer_time) 
			VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            '''

        SQLite3Connector.execute(
            config.db.l_path,
            query,
            'commit',
            False,
            log
        )

    @staticmethod
    def update_question_type(question_id: int, question_type: str):
        query = \
            '''
            update questions
            set question_type = ?
            where question_id = ?
            '''

        SQLite3Connector.execute(
            config.db.l_path,
            query,
            'commit',
            False,
            (question_type, question_id)
        )

    @staticmethod
    def update_question(question_id: int, question_text: str):
        query = \
            '''
            update questions
            set text = ?
            where question_id = ?
            '''

        SQLite3Connector.execute(
            config.db.l_path,
            query,
            'commit',
            False,
            (question_text, question_id)
        )
    
    @staticmethod
    def remove_question(question_id: int):

        '''
        удаляет вопрос из БД по его id,
        а также все связанные с ним ответы
        '''
        pass

        # сначала удаляем вопрос
        query = \
            '''
            delete
            from questions
            where question_id = ?
            '''

        SQLite3Connector.execute(
            config.db.l_path,
            query,
            'commit',
            False,
            (question_id,)
        )

        # а потом удаляем ответы
        query = \
            '''
            delete
            from answers
            where question_id = ?
            '''

        SQLite3Connector.execute(
            config.db.l_path,
            query,
            'commit',
            False,
            (question_id,)
        )

    @staticmethod
    def add_answer(question_id: int, answer_text: str, right: int):
        query = \
            '''
            insert into answers
            (question_id, text, right)
             values (?,?,?)
            '''

        SQLite3Connector.execute(
            config.db.l_path,
            query,
            'commit',
            False,
            (question_id, answer_text, right)
        )
    
    def add_question(set_id: int, account_id: str, question_text: int) -> int:
        query = \
            '''
            insert into questions
            (set_id, account_id, text)
            values (?,?,?)
            returning question_id;
            '''

        return SQLite3Connector.execute(
            config.db.l_path,
            query,
            'returning',
            False,
            (set_id, account_id, question_text)
        )[0]
    
    def create_set(set_name) -> int:
        query = \
        '''
        insert into sets (set_name) values (?) returning set_id;
        '''

        return SQLite3Connector.execute(config.db.l_path,
                          query,
                          request_type = 'returning',
                          args = (set_name,))[0]

    @staticmethod
    def update_answer(answer_id: int, answer_text: str, right: int) -> None:
        query = \
            '''
            update answers
            set text = ?, right = ?
            where answer_id = ?
            '''

        return SQLite3Connector.execute(
            config.db.l_path,
            query,
            'commit',
            False,
            (answer_text, right, answer_id)
        )

    @staticmethod
    def get_sets_by_account(account_id: int) -> list:
        
        '''
        returns all sets that are used in accound_id (set_id, set_name)
        '''
        # query = \
        #     '''
        #     select distinct sets.set_id, sets.set_name from sets 
        #     join questions on questions.set_id = sets.set_id
        #     where questions.account_id = ?;
        #     '''
        query = \
            '''
            select 
                set_id, set_name
            from 
                sets
            where 
                account_id = ?
            '''


        return SQLite3Connector.execute(
            config.db.l_path,
            query,
            'fetchall',
            False,
            (account_id,)
        )

        # return [row[0] for row in result]
