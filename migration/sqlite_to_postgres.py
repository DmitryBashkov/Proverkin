'''
Скрипт миграции данных из старой SQLite БД (Proverkin v1) в Postgres
новой микросервисной версии.

Использование:
    pip install psycopg[binary]
    python sqlite_to_postgres.py \
        --sqlite /path/to/old/proverkin.sqlite \
        --dsn postgresql://proverkin:proverkin@localhost:5432/proverkin

Идемпотентность: скрипт переносит accounts/users/sets/questions/answers/
user_sets/logs. Если PK совпадет с уже существующим -- пропускает строку.
В Postgres схеме после прогона нужно поднять sequence'ы (в конце скрипта
это делается автоматически).
'''

import argparse
import logging
import sqlite3
import sys

import psycopg

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('migration')


# Карта таблиц: (имя, список колонок в исходном порядке).
# Если в SQLite не было какой-то колонки -- она добавится со значением null.

TABLES = [
    ('accounts',  ['account_id', 'account_name']),
    ('users',     ['user_id', 'account_id', 'telegram_username', 'chat_id',
                   'real_name', 'user_type', 'active']),
    ('sets',      ['set_id', 'account_id', 'set_name']),
    ('questions', ['question_id', 'set_id', 'account_id', 'text', 'question_type']),
    ('answers',   ['answer_id', 'question_id', 'text', 'right']),
    ('user_sets', ['user_id', 'set_id', 'qty']),
    ('logs',      ['log_id', 'quiz_date', 'account_id', 'user_id', 'real_name',
                   'telegram_username', 'set_id', 'set_name', 'question_id',
                   'question_text', 'result', 'answer_text', 'answer_time']),
]


def fetch_sqlite(conn: sqlite3.Connection, table: str, columns: list) -> list:
    cur = conn.cursor()
    cur.execute(f'pragma table_info({table})')
    existing = {row[1] for row in cur.fetchall()}
    if not existing:
        logger.warning(f'В SQLite нет таблицы {table} -- пропускаем')
        return []

    select_cols = []
    for c in columns:
        if c in existing:
            # quote 'right' which is reserved
            select_cols.append(f'"{c}"' if c == 'right' else c)
        else:
            select_cols.append('NULL')

    sql = f'select {", ".join(select_cols)} from {table}'
    cur.execute(sql)
    return cur.fetchall()


def insert_postgres(pg_conn: psycopg.Connection, table: str,
                    columns: list, rows: list) -> int:
    if not rows:
        return 0
    cols_quoted = [f'"{c}"' if c == 'right' else c for c in columns]
    placeholders = ', '.join(['%s'] * len(columns))
    sql = (
        f'insert into {table} ({", ".join(cols_quoted)}) '
        f'values ({placeholders}) on conflict do nothing'
    )
    inserted = 0
    with pg_conn.cursor() as cur:
        for row in rows:
            cur.execute(sql, row)
            inserted += cur.rowcount
    return inserted


def fix_sequences(pg_conn: psycopg.Connection) -> None:
    sql_pairs = [
        ('accounts',  'account_id'),
        ('users',     'user_id'),
        ('sets',      'set_id'),
        ('questions', 'question_id'),
        ('answers',   'answer_id'),
        ('logs',      'log_id'),
    ]
    with pg_conn.cursor() as cur:
        for table, pk in sql_pairs:
            cur.execute(
                f"select setval(pg_get_serial_sequence('{table}', '{pk}'), "
                f"coalesce((select max({pk}) from {table}), 1))"
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sqlite', required = True, help = 'Path to old SQLite file')
    parser.add_argument('--dsn', required = True, help = 'Postgres DSN')
    args = parser.parse_args()

    sq = sqlite3.connect(args.sqlite)

    with psycopg.connect(args.dsn) as pg:
        with pg.transaction():
            total = 0
            for table, columns in TABLES:
                rows = fetch_sqlite(sq, table, columns)
                inserted = insert_postgres(pg, table, columns, rows)
                logger.info(f'{table}: прочитано {len(rows)}, вставлено {inserted}')
                total += inserted
            fix_sequences(pg)
            logger.info(f'Готово. Всего вставлено {total} строк, sequence-ы обновлены.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f'Migration failed: {e}')
        sys.exit(1)
