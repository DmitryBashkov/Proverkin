'''
Дополнительные admin-методы для web_gui.
Стиль -- такой же, как PostgresConnector (статические методы).
'''

from database.connector import PostgresConnector as pg


class Admin:

    # ====== accounts ======

    @staticmethod
    def list_accounts() -> list:
        return pg.execute(
            'select account_id, account_name from accounts order by account_id',
            'fetchall'
        ) or []

    @staticmethod
    def add_account(name: str) -> int:
        return pg.execute(
            'insert into accounts (account_name) values (%s) returning account_id',
            'returning', (name,)
        )[0]

    # ====== users ======

    @staticmethod
    def list_users() -> list:
        '''
        Возвращает (user_id, telegram_username, chat_id, real_name,
                    user_type, account_id, account_name, active)
        '''
        return pg.execute(
            '''
            select u.user_id, u.telegram_username, u.chat_id, u.real_name,
                   u.user_type, u.account_id, a.account_name, u.active
            from users u
            left join accounts a on a.account_id = u.account_id
            order by u.user_id
            ''',
            'fetchall'
        ) or []

    @staticmethod
    def get_user_full(user_id: int) -> tuple:
        return pg.execute(
            '''
            select user_id, telegram_username, chat_id, real_name,
                   user_type, account_id, active
            from users
            where user_id = %s
            ''',
            'fetchone', (user_id,)
        )

    @staticmethod
    def create_user(telegram_username: str, real_name: str,
                    account_id: int, user_type: str = 'user',
                    active: int = 1) -> int:
        return pg.add_user(
            telegram_username = telegram_username,
            real_name = real_name,
            account_id = account_id,
            user_type = user_type,
            active = active
        )

    @staticmethod
    def edit_user(user_id: int, telegram_username: str, real_name: str,
                  account_id: int, user_type: str, active: int) -> None:
        pg.execute(
            '''
            update users
            set telegram_username = %s,
                real_name = %s,
                account_id = %s,
                user_type = %s,
                active = %s
            where user_id = %s
            ''',
            'commit',
            (telegram_username, real_name, account_id, user_type, active, user_id)
        )

    @staticmethod
    def delete_user(user_id: int) -> None:
        pg.execute('delete from users where user_id = %s', 'commit', (user_id,))

    # ====== sets ======

    @staticmethod
    def list_sets(account_id: int = None) -> list:
        '''
        Возвращает (set_id, set_name, account_id, generator_prompt,
                    generator_model, target_pool_size).
        '''
        if account_id is None:
            return pg.execute(
                '''
                select set_id, set_name, account_id, generator_prompt,
                       generator_model, target_pool_size
                from sets
                order by set_id
                ''',
                'fetchall'
            ) or []
        return pg.execute(
            '''
            select set_id, set_name, account_id, generator_prompt,
                   generator_model, target_pool_size
            from sets where account_id = %s
            order by set_id
            ''',
            'fetchall', (account_id,)
        ) or []

    @staticmethod
    def get_set(set_id: int) -> tuple:
        return pg.execute(
            '''
            select set_id, set_name, account_id, generator_prompt,
                   generator_model, target_pool_size
            from sets where set_id = %s
            ''',
            'fetchone', (set_id,)
        )

    @staticmethod
    def create_set(account_id: int, set_name: str,
                   generator_prompt: str = None,
                   generator_model: str = None,
                   target_pool_size: int = 0) -> int:
        return pg.execute(
            '''
            insert into sets
                (account_id, set_name, generator_prompt, generator_model, target_pool_size)
            values (%s, %s, %s, %s, %s)
            returning set_id
            ''',
            'returning',
            (account_id, set_name,
             generator_prompt or None,
             generator_model or None,
             int(target_pool_size or 0))
        )[0]

    @staticmethod
    def edit_set(set_id: int, set_name: str,
                 generator_prompt: str = None,
                 generator_model: str = None,
                 target_pool_size: int = 0) -> None:
        pg.execute(
            '''
            update sets
            set set_name = %s,
                generator_prompt = %s,
                generator_model = %s,
                target_pool_size = %s
            where set_id = %s
            ''',
            'commit',
            (set_name,
             generator_prompt or None,
             generator_model or None,
             int(target_pool_size or 0),
             set_id)
        )

    @staticmethod
    def delete_set(set_id: int) -> None:
        pg.execute('delete from sets where set_id = %s', 'commit', (set_id,))

    # ====== user_sets (привязки) ======

    @staticmethod
    def list_user_sets(user_id: int) -> list:
        return pg.execute(
            '''
            select us.set_id, s.set_name, us.qty
            from user_sets us
            join sets s on s.set_id = us.set_id
            where us.user_id = %s
            order by s.set_name
            ''',
            'fetchall', (user_id,)
        ) or []

    @staticmethod
    def upsert_user_set(user_id: int, set_id: int, qty: int) -> None:
        pg.execute(
            '''
            insert into user_sets (user_id, set_id, qty)
            values (%s, %s, %s)
            on conflict (user_id, set_id) do update set qty = excluded.qty
            ''',
            'commit', (user_id, set_id, qty)
        )

    @staticmethod
    def remove_user_set(user_id: int, set_id: int) -> None:
        pg.execute(
            'delete from user_sets where user_id = %s and set_id = %s',
            'commit', (user_id, set_id)
        )

    # ====== очередь ======

    @staticmethod
    def list_queue(set_id: int = None, status: str = None) -> list:
        '''
        Возвращает (item_id, set_id, set_name, status, model, payload, created_at)
        '''
        sql = \
        '''
        select gq.item_id, gq.set_id, s.set_name, gq.status, gq.model,
               gq.payload, gq.created_at
        from generation_queue gq
        join sets s on s.set_id = gq.set_id
        where 1 = 1
        '''
        args = []
        if set_id is not None:
            sql += ' and gq.set_id = %s'
            args.append(set_id)
        if status is not None:
            sql += ' and gq.status = %s'
            args.append(status)
        sql += ' order by gq.item_id desc limit 200'
        return pg.execute(sql, 'fetchall', tuple(args)) or []

    @staticmethod
    def queue_promote_to_questions(item_id: int) -> int:
        '''
        Берет элемент очереди и создает из него запись в questions+answers.
        Возвращает question_id. Помечает элемент как 'approved'.
        '''
        row = pg.execute(
            '''
            select set_id, account_id, payload from generation_queue
            where item_id = %s
            ''',
            'fetchone', (item_id,)
        )
        if not row:
            return None
        set_id, account_id, payload = row

        # payload приходит уже распарсенным dict из jsonb
        question_text = payload['question']
        answers = payload['answers']

        question_id = pg.add_question(set_id, account_id, question_text, source = 'ai')
        for a in answers:
            pg.add_answer(question_id, a['text'], int(bool(a.get('right'))))

        pg.execute(
            '''update generation_queue set status = 'approved' where item_id = %s''',
            'commit', (item_id,)
        )

        return question_id

    @staticmethod
    def queue_reject(item_id: int) -> None:
        pg.execute(
            '''update generation_queue set status = 'rejected' where item_id = %s''',
            'commit', (item_id,)
        )

    # ====== логи квиза ======

    @staticmethod
    def recent_logs(limit: int = 100) -> list:
        return pg.execute(
            '''
            select created_at, real_name, telegram_username,
                   set_name, question_text, result, answer_text, answer_time
            from logs
            order by log_id desc
            limit %s
            ''',
            'fetchall', (limit,)
        ) or []
