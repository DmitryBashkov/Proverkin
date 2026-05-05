-- =====================================================================
-- Proverkin :: схема БД для микросервисной версии
-- =====================================================================
-- Сохраняем максимально близко имена таблиц/полей из исходного проекта,
-- чтобы было удобно мигрировать данные и не переписывать половину кода.
-- Добавлены только две новые таблицы для очереди сгенерированных
-- вопросов и для тематических заданий генератора.
-- =====================================================================

-- ========== базовые сущности ==========

create table if not exists accounts (
    account_id      serial primary key,
    account_name    text not null,
    created_at      timestamptz not null default now()
);

create table if not exists sets (
    set_id          serial primary key,
    account_id      integer not null references accounts(account_id) on delete cascade,
    set_name        text not null,
    -- параметры генератора (если null -- генератор сет не трогает)
    generator_prompt    text,
    generator_model     text,
    target_pool_size    integer not null default 0,
    created_at      timestamptz not null default now()
);

create index if not exists ix_sets_account on sets(account_id);

create table if not exists users (
    user_id             serial primary key,
    account_id          integer references accounts(account_id) on delete set null,
    telegram_username   text,
    chat_id             bigint unique,
    real_name           text,
    user_type           text not null default 'user',
    active              integer not null default 1,
    created_at          timestamptz not null default now()
);

create index if not exists ix_users_username on users(telegram_username);
create index if not exists ix_users_account on users(account_id);

create table if not exists user_sets (
    user_id     integer not null references users(user_id) on delete cascade,
    set_id      integer not null references sets(set_id) on delete cascade,
    qty         integer not null default 3,
    primary key (user_id, set_id)
);

-- ========== вопросы и ответы ==========

create table if not exists questions (
    question_id     serial primary key,
    set_id          integer not null references sets(set_id) on delete cascade,
    account_id      integer references accounts(account_id) on delete set null,
    text            text not null,
    question_type   text not null default 'normal',
    -- источник: 'manual' или 'ai'
    source          text not null default 'manual',
    created_at      timestamptz not null default now()
);

create index if not exists ix_questions_set on questions(set_id);

create table if not exists answers (
    answer_id       serial primary key,
    question_id     integer not null references questions(question_id) on delete cascade,
    text            text not null,
    "right"         integer not null default 0
);

create index if not exists ix_answers_question on answers(question_id);

-- ========== логи прохождения квиза ==========

create table if not exists logs (
    log_id              serial primary key,
    quiz_date           date not null,
    account_id          integer,
    user_id             integer,
    real_name           text,
    telegram_username   text,
    set_id              integer,
    set_name            text,
    question_id         integer,
    question_text       text,
    result              integer,
    answer_text         text,
    answer_time         double precision,
    created_at          timestamptz not null default now()
);

create index if not exists ix_logs_user on logs(user_id);
create index if not exists ix_logs_date on logs(quiz_date);

-- ========== очередь генератора ==========
-- Generator-service кладет сюда заранее сгенерированные вопросы.
-- Quiz-service и web-gui потом могут их "промоутить" в questions
-- (или генератор делает это сам -- зависит от настроек set'а).

create table if not exists generation_queue (
    item_id         serial primary key,
    set_id          integer not null references sets(set_id) on delete cascade,
    account_id      integer,
    -- сам пэйлоад: текст вопроса + варианты ответа в JSON
    payload         jsonb not null,
    -- статус: 'pending' (ждет одобрения), 'approved' (уже в questions),
    -- 'rejected', 'consumed' (использован для пополнения questions)
    status          text not null default 'pending',
    -- какая модель сгенерила
    model           text,
    created_at      timestamptz not null default now(),
    consumed_at     timestamptz
);

create index if not exists ix_queue_set_status on generation_queue(set_id, status);

-- ========== начальные данные ==========

insert into accounts (account_id, account_name)
values (0, 'trial'), (1, 'default')
on conflict (account_id) do nothing;

-- сдвигаем sequence, чтобы после ручной вставки accounts с id=0,1
-- следующий serial начинался с 2
select setval('accounts_account_id_seq', greatest((select max(account_id) from accounts), 1));
