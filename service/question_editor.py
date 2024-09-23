# openpyxl
import openpyxl as op
from openpyxl import Workbook
from openpyxl.styles import Protection, Alignment
from openpyxl.worksheet.protection import SheetProtection
from openpyxl.styles import PatternFill, Font

# project
from database.connector import SQLite3Connector as sqlite3_connector
from service.question import QuestionSet
from config_data.config import config
from utils.misc import replace_space

# misc
import re
import datetime




class Excel():
    header = ['q_id', 'Вопрос', 'r_num']

    def download_questions(account_id: int) -> str:

        # создаем новую книгу
        wb = Workbook()

        # получаем наименование клиента
        account_name = replace_space(sqlite3_connector.get_account_name(account_id))

        # получаем все сеты, которые привязаны к этому клиенту
        sets = sqlite3_connector.get_sets_by_account(account_id)

        # хэдер для вкладки пользователей
        # тут мы сразу записываем set_id и set_name
        sets_header = []

        for set_ in sets:
            # записываем в хэдер "сет (номер сета)"
            sets_header.append(f'{set_[1]} ({set_[0]})')
            Excel._create_questions_worksheet(wb, set_)

        # удаляем первый sheet (он появился при создании книги)
        wb.remove(wb.worksheets[0])

        Excel._create_user_worksheet(account_id, wb, sets_header)
        
        # сохраняем файл
        file_name = f'{config.export_file_storage}update_{account_id}_{account_name}_{datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.xlsx'
        wb.save(file_name)

        return file_name

    def _create_user_worksheet(account_id, wb, sets_header):
        
        # создаем новую вкладку с пользователями
        user_ws = wb.create_sheet('Пользователи')

        # добавляем хэдер с сетами в основной хэдер
        header = ['user_id', 'Telegram', 'ФИО', 'Активен', *sets_header]

        user_ws.append(header)

        # проходим по каждому пользователю
        for user in sqlite3_connector.get_all_users_by_account_id(account_id):
            # массив, который мы будем добавлять в качестве строки в таблицу для каждого пользователя
            append_row = []
            append_row.append(user[0])  # user_id
            append_row.append(user[1]) # telegram username
            append_row.append(user[2]) # real name

            # активность пользователя лучше обозначать словами, а не единицей
            append_row.append('Активен' if user[3] else 'Неактивен')

            # расширяем массив до количетва сетов
            append_row.extend([''] * len(sets_header))

            # проходим по каждому сету пользователя
            for user_sets in sqlite3_connector.get_users_set_list(user_id = user[0]):
                index = sets_header.index(f'{user_sets[1]} ({user_sets[0]})')
                append_row[4+index] = user_sets[2]

            # добавляем запись о пользователе
            user_ws.append(append_row)

    def _create_questions_worksheet(wb, set_):

        # создаем новый лист в таблице с названием "сет и (номер сета)"
        ws = wb.create_sheet(f'{set_[1]} ({set_[0]})')

        # переменная для подсчета количества ответов. Нужна, чтобы верно сформировать хэдер таблицы
        max_answers = 0

        # получаем массив объектов с вопросами
        question_set = QuestionSet(set_[0])

        # добавляем весь вопрос с ответами в таблицу, 
        # заодно считаем кол-во максимальных ответов
        for question in question_set.questions:
            ws.append(question._form_row())
            max_answers = max(max_answers, len(question.answers))

        # задаем хэдер для таблицы
        header = ['q_id', 'Вопрос', 'Количество правильных ответов']

        # дописываем столбцы с ответами по максимальному количеству ответов
        for i in range(1, max_answers+1):
            header.append('a_id')
            header.append(f'Ответ - {i}')
            
        # добавляем строку для хедера
        if len(question_set.questions) == 0:
            ws.append(header)
        else:
            ws.insert_rows(1)

        # форматируем хедер
        for row in ws.iter_rows(min_row = 1, max_col = ws.max_column, max_row = 1):
            for index, cell in enumerate(row):
                
                # даем название заголовкам
                cell.value = header[index]

                # жирный и подчеркнутый текст, размер 12
                cell.font = Font(bold = True, 
                                     underline = 'single',
                                     size = 12)
                    
                # серый фон
                cell.fill = PatternFill(start_color='D3D3D3', 
                                            end_color='D3D3D3', 
                                            fill_type='solid')

                # выравнивание по центру и перенос строки
                cell.alignment = Alignment(wrap_text = True, 
                                              vertical = 'center', 
                                              horizontal = 'center')

                # если у нас в столбце хранится id то мы его скрываем
                if cell.value.find('id') >= 0:
                    ws.column_dimensions[op.utils.cell.get_column_letter(index+1)].hidden = True
                        
                # все остальные столбцы с фиксированной шириной
                else:
                    
                    # для столбца с количеством правильных ответов ширина
                    if index+1 == 3:
                        ws.column_dimensions[op.utils.cell.get_column_letter(index+1)].width = 15
                        
                    # для столбцов с вопросами 
                    else:
                        ws.column_dimensions[op.utils.cell.get_column_letter(index+1)].width = 300 / 7
                        
                    ws.column_dimensions[op.utils.cell.get_column_letter(index+1)].auto_size = False

                    # разблокируем ячейки, которые может редактировать пользователь
                    for unlock_cells in ws[op.utils.cell.get_column_letter(index+1)]:

                        # разблокируем все, что ниже 1-й строчки
                        if unlock_cells.row > 1:
                            unlock_cells.protection = Protection(locked = False)
                            
                            # центрируем столбец с количеством правильных ответов
                            if unlock_cells.column == 3:
                                unlock_cells.alignment = Alignment(wrap_text = True, 
                                                                       vertical = 'center', 
                                                                       horizontal = 'center')
                            # все остальные просто вертикальное выравнивание по центру
                            else:
                                unlock_cells.alignment = Alignment(wrap_text = True, 
                                                                       vertical = 'top')
                                    
                    ws.column_dimensions[op.utils.cell.get_column_letter(index+1)].protection = Protection(locked = False)

        # задаем формат защиты (все нельзя)
        protection = SheetProtection(sheet=True, objects=True, scenarios=True,
                                 formatCells=True, formatColumns=True, formatRows=True,
                                 insertColumns=True, insertRows=True, insertHyperlinks=True,
                                 deleteColumns=True, deleteRows=True, selectLockedCells=True,
                                 sort=True, autoFilter=True, pivotTables=True)
    
        # Разрешаем изменение размера столбцов
        protection.formatRows = False
            
        # Применяем защиту к листу
        ws.protection = protection

    def upload_questions(account_id: int, file_path: str) -> None:

        # открываем книгу
        wb = op.load_workbook(file_path)


        users_ws = wb['Пользователи']

        # проверяем, есть ли лист с пользователями
        if users_ws != None:
            Excel._update_users(users_ws, account_id)

        # проходим по каждому листу
        for sheet in wb.worksheets:

            if sheet.title == 'Пользователи':
                continue

            set_id = 0

            # ищем N в "Название (N)"
            match = re.search(r"\((\d+)\)" , sheet.title)

            # если находим, то это и есть наш сет id
            if match:
                set_id = match.group(1)

            # если не находим, то надо создавать сет в бд
            else:
                set_id = sqlite3_connector.create_set(sheet.title)

            set_title = sheet.title

            # удаляем хедер
            sheet.delete_rows(0)

            # проходим по каждой строчке (берем только значения ячеек)
            for row in sheet.iter_rows(values_only = True):

                if not any(row):
                    continue

                question_id = row[0]
                question_text = row[1]
                right_answers_count = int(row[2])

                # если у вопроса есть id 
                # (то есть мы редактируем существующий)
                if type(question_id) == int:
                    
                    # если есть id, но нет текста, 
                    # значит пользователь удалил вопрос
                    if question_text is None or len(question_text.replace(' ','')) == 0:
                        sqlite3_connector.remove_question(question_id)
                        continue # продолжать смысла нет, тк мы уже удалили все ответы
                    
                    # если текст вопроса есть, мы его обновляем в бд,
                    # тк пользователь мог его отредактировать
                    else:
                        sqlite3_connector.update_question(question_id, question_text)
                
                # если у вопроса нет id, 
                # значит это новый вопрос, 
                # и его надо добавить в БД
                else:
                    question_id = sqlite3_connector.add_question(set_id, account_id, question_text)
                

                # идем по ответам на вопросы
                # с шагом 2 (тк на каждый ответ есть текст и id)
                for i in range(3, len(row), 2):
                    answer_id = row[i]
                    answer_text = row[i+1]

                    # эта строчка временная, на случай, если пользователь
                    # поставит количество правильных ответов больше 1
                    # в будущем переменная должна просто брать значение без условий
                    right = 1 if right_answers_count > 0 else 0

                    if type(answer_id) == int:
                        sqlite3_connector.update_answer(answer_id, answer_text, right)
                    elif answer_text != None:
                        sqlite3_connector.add_answer(question_id, answer_text, right)

                    # снижаем количество правильных ответов
                    right_answers_count -= 1

    def _update_users(users_ws, account_id):

        # получаем хедер
        header = [cell.value for cell in next(users_ws.iter_rows(min_row=1, max_row=1))]

        # переименовываем названия сетов, оставляет в ячейках только их id
        for set_ in header[4:]:
            header[header.index(set_)] = int(re.search(r"\((\d+)\)" , set_).group(1))

        header = header[4:]

        # удаляем хедер в excel
        users_ws.delete_rows(0)

        # проходим по всем пользователям
        for row in users_ws.iter_rows(values_only = True):

            # присваиваем значения
            user_id = row[0]                            # id пользователя
            telegram_username = row[1]                  # логин в телеграме
            real_name = row[2]                          # ФИО
            active = 0 if row[3] == 'Неактивен' else 1  # активен или нет (1,0)

            # если в ячейке нет user_id, значит это новый пользовтель
            if user_id == None:
                user_id = sqlite3_connector.add_user(telegram_username = telegram_username,
                                                     real_name = real_name,
                                                     account_id = account_id,
                                                     active = active)

            # если есть, то обновляем текущего   
            else:
                sqlite3_connector.update_user(user_id = user_id,
                                              telegram_username = telegram_username,
                                              real_name = real_name,
                                              active = active)
            
            # идем дальеш по сетам
            for i, qty in enumerate(row[4:]):
                sqlite3_connector.set_set_qty(user_id = user_id, set_id = header[i], qty = qty)
















        