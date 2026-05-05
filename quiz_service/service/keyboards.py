'''
Билдеры клавиатур.

Возвращают dict в формате, который понимает bot_service.
Структура:
    {
        "rows": [
            [{"text": "...", "callback_data": "..."}],
            [{"text": "...", "callback_data": "..."}, ...],
            ...
        ]
    }

Bot_service из этого собирает InlineKeyboardMarkup.

Callback data -- наша собственная сериализация (см. callbacks.py),
формата "ns:k1=v1;k2=v2".
'''

import random

from service.question import Question
from service.messages import READY


# ====== формат callback ======

def encode_callback(ns: str, **kwargs) -> str:
    '''
    'quiz' + {right=1, id_=42, q=10}  ->  'quiz:right=1;id_=42;q=10'
    Telegram ограничивает callback_data 64 байтами, поэтому
    короткие ключи -- сознательно.
    '''
    parts = []
    for k, v in kwargs.items():
        parts.append(f'{k}={v}')
    return f'{ns}:' + ';'.join(parts)


def decode_callback(data: str) -> tuple[str, dict]:
    if ':' not in data:
        return data, {}
    ns, rest = data.split(':', 1)
    out = {}
    if rest:
        for pair in rest.split(';'):
            if '=' in pair:
                k, v = pair.split('=', 1)
                out[k] = v
    return ns, out


# ====== собственно клавиатуры ======

def quiz_ready_keyboard() -> dict:
    return {
        'rows': [[
            {
                'text': random.choice(READY),
                'callback_data': encode_callback('ready')
            }
        ]]
    }


def quiz_answers_keyboard(question: Question) -> dict:
    rows = []

    random.shuffle(question.answers)

    for answer in question.answers:
        text = answer.text if not question.long_asnwers else answer.bullet
        rows.append([{
            'text': text,
            'callback_data': encode_callback(
                'quiz',
                r = int(bool(answer.right)),
                a = answer.id_,
                q = question.id,
                bad = 0
            )
        }])

    rows.append([{
        'text': '❗️Некорректный вопрос❗️',
        'callback_data': encode_callback(
            'quiz', r = 1, a = 0, q = question.id, bad = 1
        )
    }])

    # для коротких ответов делаем по 1 на строку (как в исходнике через adjust(1))
    return {'rows': rows}
