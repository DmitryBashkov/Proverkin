import matplotlib.pyplot as plt
import pandas as pd
import datetime
from typing import Literal
from aiogram.types import FSInputFile
from service.user import User


'''
Группа
==============
1. На какой вопрос чаще всего отвечают неверно
2. Правильные/неправильные ответы по дням (неделя)
'''

def get_day_stat(user: User, user_stat: str) -> FSInputFile | bool:
    pass
    # '''
    # Эта функция взята с ссылки (очень удачно попалась):
    # https://towardsdatascience.com/100-stacked-charts-in-python-6ca3e1962d2b
    # '''
    # # получаем данные из таблцы гугла и создаем DataFrame
    # stat_from_sheet = gsheet.get_users_stat(user)
    # df = pd.DataFrame(stat_from_sheet[1:], columns = stat_from_sheet[0])

    # # определяем типа данных в столбце "Дата"
    # df['Дата'] = pd.to_datetime(df['Дата'], dayfirst = True)

    # # оставляем записи только с сегодняшней датой
    # df = df[df['Дата'].dt.date == pd.Timestamp.now().date()]

    # # если в аргументе был передан конкретный пользовтаеля,
    # # то дополнительно фильтурем таблицу по нему
    # if user_stat != 'all':
    #     df = df[df['Логин'] == user_stat]

    # if df.empty:
    #     return False

    # # оставляем только два столбца 'Логин' и 'Результат'
    # df = df.loc[:,['Логин', 'Результат']]

    # # какая-то магия, которая мне пока непонятна
    # cross_tab_prop = pd.crosstab(index=df['Логин'],
    #                             columns=df['Результат'],
    #                             normalize="index")

    # # сортируем по количесту правильных ответов
    # cross_tab_prop = cross_tab_prop.sort_values('Верно')

    # # создаем график
    # cross_tab_prop.plot(kind = 'barh', stacked = True, figsize = [7, 5])

    # # сохраняем изображение, bbox_inches = 'tight' убирает лишние белые поля
    # plt.savefig('fig.png', bbox_inches = 'tight')

    # # передаем объект файла
    # file = FSInputFile('fig.png')
    # return file

def get_week_stat(user: User, user_stat: str) -> FSInputFile:
    pass
    # # получаем данные из таблцы гугла и создаем DataFrame
    # stat_from_sheet = gsheet.get_users_stat(user)
    # df = pd.DataFrame(stat_from_sheet[1:], columns = stat_from_sheet[0])

    # # оставляем записи за последнюю неделю
    # date = datetime.datetime.now() - datetime.timedelta(days = 7)
    # df = df[df['Дата'].astype('datetime64[ns]') >= date]

    # # если в аргументе был передан конкретный пользовтаеля,
    # # то дополнительно фильтурем таблицу по нему
    # if user_stat != 'all':
    #     df = df[df['Логин'] == user_stat]

    # if df.empty:
    #     return False

    # # оставляем только два столбца 'Логин' и 'Результат'
    # df = df.loc[:,['Дата', 'Результат']]

    # # какая-то магия, которая мне пока непонятна
    # cross_tab_prop = pd.crosstab(index = df['Дата'],
    #                             columns = df['Результат'],
    #                             normalize = 'index')

    # # сортируем по количесту правильных ответов
    # cross_tab_prop = cross_tab_prop.sort_values('Дата')

    # # создаем график
    # cross_tab_prop.plot(kind = 'bar', stacked = True, figsize = [5, 5], xlabel = '')
    # plt.title('Динамика правильных ответов за последние 7 дней')

    # # сохраняем изображение, bbox_inches = 'tight' убирает лишние белые поля
    # plt.savefig('fig.png', bbox_inches = 'tight')

    # # передаем объект файла
    # file = FSInputFile('fig.png')
    # return file

def get_failed_questions(user: User, user_stat: str, days: int = 7, ) -> list:
    pass
    # # получаем данные из таблцы гугла и создаем DataFrame
    # stat_from_sheet = gsheet.get_users_stat(user)
    # df = pd.DataFrame(stat_from_sheet[1:], columns = stat_from_sheet[0])

    # # оставляем записи за последнюю неделю
    # date = datetime.datetime.now() - datetime.timedelta(days = days)
    # df = df[df['Дата'].astype('datetime64[ns]') >= date]

    # # если в аргументе был передан конкретный пользовтаеля,
    # # то дополнительно фильтурем таблицу по нему
    # if user_stat != 'all':
    #     df = df[df['Логин'] == user_stat]

    # if df.empty:
    #     return False

    # # выбираем только вопросы с неправильными ответами
    # df = df[df['Результат'] == 'Неверно']

    # # оставляем только два столбца 'Логин' и 'Результат'
    # df = df.loc[:,['Вопрос (текст)', 'Результат']]

    # # какая-то магия, которая становится чуть понятнее.
    # # обновляем индекс, тк потом надо получить list.
    # # в противном случае сам вопрос будет индексом
    # cross_tab_prop = pd.crosstab(index = df['Вопрос (текст)'],
    #                          columns = df['Результат']).reset_index()

    # # сортируем по количесту неправильных ответов от большего к меньшему
    # cross_tab_prop = cross_tab_prop.sort_values('Неверно', ascending = False)

    # # переносим все в list и передаем на выход
    # return cross_tab_prop.head().values.tolist()
    