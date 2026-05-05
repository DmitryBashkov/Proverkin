import logging
from typing import Any, Literal
import json

import psycopg
from psycopg.rows import tuple_row

from config_data.config import config

logger = logging.getLogger(__name__)


class PostgresConnector:
    '''
    Тонкая обертка над psycopg.
    Стиль (статические методы, request_type, args) намеренно повторяет
    SQLite3Connector из исходного проекта, чтобы остальные модули
    меняли минимум.

    request_type:
        - 'fetchall'  -- вернуть list[tuple]
        - 'fetchone'  -- вернуть один tuple или None
        - 'commit'    -- выполнить и закоммитить
        - 'returning' -- выполнить с returning ... и вернуть один tuple
    '''

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PostgresConnector, cls).__new__(cls)
        return cls.instance

    @staticmethod
    def execute(sql_request: str,
                request_type: Literal['fetchall', 'fetchone', 'commit', 'returning'],
                args: tuple = (),
                iterator: bool = False) -> Any:

        result = None
        db_connection = None

        try:
            db_connection = psycopg.connect(config.db.dsn, row_factory = tuple_row)
            db_cursor = db_connection.cursor()

            match request_type:
                case 'fetchall':
                    db_cursor.execute(sql_request, args)
                    result = db_cursor.fetchall()

                case 'fetchone':
                    db_cursor.execute(sql_request, args)
                    result = db_cursor.fetchone()

                case 'commit':
                    db_cursor.execute(sql_request, args)
                    db_connection.commit()

                case 'returning':
                    db_cursor.execute(sql_request, args)
                    result = db_cursor.fetchone()
                    db_connection.commit()

        except psycopg.Error as error:
            logger.error(f'''Postgres execution error:\n
                        Error: {error}\n
                        SQL request: {sql_request}\n
                        Request type: {request_type}''')

        finally:
            if db_connection:
                db_connection.close()

        return result

    # ====== общие сервисные методы ======

    @staticmethod
    def init_check() -> bool:
        '''
        Проверяем, что нужные таблицы созданы. Если нет --
        предполагается, что init.sql отработал в Postgres-контейнере.
        '''
        query = \
        '''
        select table_name
        from information_schema.tables
        where table_schema = 'public'
        '''

        rows = PostgresConnector.execute(query, request_type = 'fetchall')

        if rows is None:
            return False

        table_set = set(row[0] for row in rows)

        required = {'users', 'accounts', 'sets', 'questions',
                    'answers', 'user_sets', 'logs', 'generation_queue'}

        if required.issubset(table_set):
            return True

        logger.error(f'Проверьте БД. Не хватает таблиц: {required - table_set}')
        return False

    # ====== users ======

    @staticmethod
    def add_user(telegram_username: str = None,
                 chat_id: int = None,
                 real_name: str = None,
                 user_type: str = 'user',
                 account_id: int = None,
                 active: int = 1) -> int:

        query = \
        '''
        insert into users
            (telegram_username, chat_id, real_name, user_type, account_id, active)
        values
            (%s, %s, %s, %s, %s, %s)
        returning user_id
        '''

        return PostgresConnector.execute(
            query,
            request_type = 'returning',
            args = (telegram_username, chat_id, real_name, user_type, account_id, active)
        )[0]

    @staticmethod
    def update_user(user_id: int,
                    telegram_username: str,
                    real_name: str,
                    active: int) -> None:

        query = \
        '''
        update users
        set telegram_username = %s, real_name = %s, active = %s
        where user_id = %s
        '''

        PostgresConnector.execute(
            query,
            request_type = 'commit',
            args = (telegram_username, real_name, active, user_id)
        )

    @staticmethod
    def is_admin(chat_id: int) -> bool:
        query = \
        '''
        select user_type
        from users
        where chat_id = %s
        '''

        record = PostgresConnector.execute(
            query,
            request_type = 'fetchone',
            args = (chat_id,)
        )

        if record is None:
            return False
        return record[0] == 'admin'

    @staticmethod
    def is_exist(chat_id: int) -> bool:
        query = \
        '''
        select user_id
        from users
        where chat_id = %s
        '''

        record = PostgresConnector.execute(
            query,
            request_type = 'fetchone',
            args = (chat_id,)
        )
        return record is not None

    @staticmethod
    def get_user(chat_id = None, username = None, params = None):
        '''
        returns (telegram_username, chat_id, *params)
        '''
        if params is None:
            return None

        request = \
        f'''
        select {",".join(params)}
        from users
        where
        '''

        if chat_id is not None:
            result = PostgresConnector.execute(
                request + 'chat_id = %s',
                request_type = 'fetchone',
                args = (chat_id,)
            )
            if result is not None:
                return result

        return PostgresConnector.execute(
            request + 'telegram_username = %s',
            request_type = 'fetchone',
            args = (username,)
        )

    @staticmethod
    def add_chat_id(username: str, chat_id: int) -> None:
        query = \
        '''
        update users
        set chat_id = %s
        where telegram_username = %s
        '''

        PostgresConnector.execute(
            query,
            request_type = 'commit',
            args = (chat_id, username)
        )

    @staticmethod
    def get_user_by_chat_id(chat_id: int) -> str:
        query = \
        '''
        select telegram_username
        from users
        where chat_id = %s
        '''

        record = PostgresConnector.execute(
            query,
            request_type = 'fetchone',
            args = (chat_id,)
        )
        return record[0] if record else None

    @staticmethod
    def get_account_id_by_chat_id(chat_id: int) -> int:
        query = \
        '''
        select account_id
        from users
        where chat_id = %s
        '''

        record = PostgresConnector.execute(
            query,
            request_type = 'fetchone',
            args = (chat_id,)
        )
        return record[0] if record else None

    @staticmethod
    def get_user_qty() -> int:
        query = 'select count(*) from users'

        record = PostgresConnector.execute(
            query,
            request_type = 'fetchone'
        )
        return record[0] if record else 0

    @staticmethod
    def get_all_active_users_with_chat_id() -> list:
        query = \
        '''
        select telegram_username, chat_id
        from users
        where chat_id is not null and active = 1
        '''

        return PostgresConnector.execute(
            query,
            request_type = 'fetchall'
        ) or []

    # ====== sets / user_sets ======

    @staticmethod
    def get_users_set_list(chat_id: int = None, user_id: int = None) -> list:
        '''
        returns (set_id, set_name, qty) for user by chat_id or user_id
        '''
        field = 'users.chat_id' if chat_id is not None else 'users.user_id'
        query = \
        f'''
        select sets.set_id, sets.set_name, user_sets.qty
        from users
        join user_sets on user_sets.user_id = users.user_id
        join sets on sets.set_id = user_sets.set_id
        where {field} = %s
        '''

        return PostgresConnector.execute(
            query,
            request_type = 'fetchall',
            args = (chat_id if chat_id is not None else user_id,)
        ) or []

    @staticmethod
    def user_has_sets(chat_id: int) -> bool:
        query = \
        '''
        select user_sets.set_id
        from user_sets
        join users on users.user_id = user_sets.user_id
        where users.chat_id = %s
        '''

        result = PostgresConnector.execute(
            query,
            request_type = 'fetchall',
            args = (chat_id,)
        )
        return bool(result)

    # ====== questions ======

    @staticmethod
    def get_question_ids_by_set_id(set_id: int) -> list:
        query = \
        '''
        select question_id from questions where set_id = %s
        '''

        result = PostgresConnector.execute(
            query,
            request_type = 'fetchall',
            args = (set_id,)
        ) or []

        return [row[0] for row in result]

    @staticmethod
    def get_question_text(question_id: int) -> str:
        query = \
        '''
        select text from questions where question_id = %s
        '''

        record = PostgresConnector.execute(
            query,
            request_type = 'fetchone',
            args = (question_id,)
        )
        return record[0] if record else None

    @staticmethod
    def get_answers(question_id: int = None, answer_id: int = None, right: bool = None) -> list:
        if question_id is None:
            if answer_id is None:
                return []

            query = \
            '''
            select text from answers where answer_id = %s order by "right" desc
            '''
            return PostgresConnector.execute(
                query, 'fetchall', (answer_id,)
            ) or []

        if right is not None:
            query = \
            '''
            select text from answers where question_id = %s and "right" = %s
            '''
            return PostgresConnector.execute(
                query, 'fetchall', (question_id, int(right))
            ) or []

        query = \
        '''
        select answer_id, text, "right" from answers where question_id = %s
        '''
        return PostgresConnector.execute(
            query, 'fetchall', (question_id,)
        ) or []

    @staticmethod
    def update_question_type(question_id: int, question_type: str) -> None:
        query = \
        '''
        update questions
        set question_type = %s
        where question_id = %s
        '''

        PostgresConnector.execute(
            query, 'commit', (question_type, question_id)
        )

    @staticmethod
    def add_question(set_id: int, account_id: int, question_text: str,
                     source: str = 'manual') -> int:
        query = \
        '''
        insert into questions (set_id, account_id, text, source)
        values (%s, %s, %s, %s)
        returning question_id
        '''

        return PostgresConnector.execute(
            query, 'returning',
            (set_id, account_id, question_text, source)
        )[0]

    @staticmethod
    def add_answer(question_id: int, answer_text: str, right: int) -> None:
        query = \
        '''
        insert into answers (question_id, text, "right")
        values (%s, %s, %s)
        '''

        PostgresConnector.execute(
            query, 'commit',
            (question_id, answer_text, right)
        )

    # ====== logs ======

    @staticmethod
    def add_log(log: list) -> None:
        '''
        log = [quiz_date, account_id, user_id, real_name, telegram_username,
               set_id, set_name, question_id, question_text, result,
               answer_text, answer_time]
        '''
        query = \
        '''
        insert into logs
            (quiz_date, account_id, user_id, real_name, telegram_username,
             set_id, set_name, question_id, question_text, result,
             answer_text, answer_time)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        '''

        PostgresConnector.execute(
            query, 'commit', tuple(log)
        )

    @staticmethod
    def get_log_data(question_id: int, chat_id: int) -> list:
        query = \
        '''
        select account_id, user_id, real_name, telegram_username
        from users
        where chat_id = %s
        '''

        user_part = PostgresConnector.execute(
            query, 'fetchone', (chat_id,)
        )

        query = \
        '''
        select sets.set_id, sets.set_name, questions.question_id, questions.text
        from questions
        join sets on sets.set_id = questions.set_id
        where questions.question_id = %s
        '''

        question_part = PostgresConnector.execute(
            query, 'fetchone', (question_id,)
        )

        return list(user_part or ()) + list(question_part or ())

    # ====== generation_queue ======

    @staticmethod
    def queue_pending_count(set_id: int) -> int:
        query = \
        '''
        select count(*) from generation_queue
        where set_id = %s and status = 'pending'
        '''

        record = PostgresConnector.execute(
            query, 'fetchone', (set_id,)
        )
        return record[0] if record else 0

    @staticmethod
    def queue_pop_one(set_id: int) -> dict:
        '''
        Атомарно достает одну запись со статусом pending из очереди для set_id
        и помечает ее как consumed. Использует SELECT ... FOR UPDATE SKIP LOCKED,
        чтобы несколько воркеров не доставали одну и ту же запись.
        '''
        db_connection = None
        try:
            db_connection = psycopg.connect(config.db.dsn, row_factory = tuple_row)
            cur = db_connection.cursor()

            cur.execute(
                '''
                select item_id, payload
                from generation_queue
                where set_id = %s and status = 'pending'
                order by item_id
                for update skip locked
                limit 1
                ''',
                (set_id,)
            )
            row = cur.fetchone()

            if row is None:
                db_connection.commit()
                return None

            item_id, payload = row

            cur.execute(
                '''
                update generation_queue
                set status = 'consumed', consumed_at = now()
                where item_id = %s
                ''',
                (item_id,)
            )
            db_connection.commit()

            return {'item_id': item_id, 'payload': payload}

        except psycopg.Error as error:
            logger.error(f'queue_pop_one error: {error}')
            return None
        finally:
            if db_connection:
                db_connection.close()

    @staticmethod
    def queue_push(set_id: int, account_id: int, payload: dict, model: str) -> int:
        query = \
        '''
        insert into generation_queue (set_id, account_id, payload, model, status)
        values (%s, %s, %s::jsonb, %s, 'pending')
        returning item_id
        '''

        return PostgresConnector.execute(
            query, 'returning',
            (set_id, account_id, json.dumps(payload, ensure_ascii = False), model)
        )[0]

    @staticmethod
    def get_generator_sets() -> list:
        '''
        Возвращает все sets, у которых задан generator_prompt и target_pool_size > 0.
        Это сигнал генератору -- набор нужно поддерживать.
        '''
        query = \
        '''
        select set_id, account_id, set_name, generator_prompt,
               generator_model, target_pool_size
        from sets
        where generator_prompt is not null
          and target_pool_size > 0
        '''

        return PostgresConnector.execute(query, 'fetchall') or []
