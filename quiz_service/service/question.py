# project
from database.connector import PostgresConnector as pg

# misc
import random
from dataclasses import dataclass


@dataclass
class Answer:
    id_: int
    text: str
    right: bool
    bullet: str


class Question:

    def __init__(self, question_id: int, for_quiz: bool = True):

        self.id = question_id
        self.thesis = None
        self.text = pg.get_question_text(question_id)

        self.answers: list[Answer] = []
        for answer in pg.get_answers(question_id):
            self.answers.append(Answer(
                id_ = answer[0],
                text = answer[1],
                right = bool(answer[2]),
                bullet = ''
            ))

        if for_quiz:
            random.shuffle(self.answers)

        '''
        Если хотя бы один из ответов длинный, переносим тексты ответов
        в сам вопрос, а на кнопках оставляем bullet'ы.
        '''

        self.long_asnwers = False

        if for_quiz:
            for answer in self.answers:
                if len(answer.text) > 35:
                    self._shorten_question()
                    self.long_asnwers = True
                    break

    def _shorten_question(self):
        number_bullets_set = ['🐶', '🐱', '🐸', '🦄', '🐥', '🐌', '🐻', '🐼', '🐷']

        random.shuffle(number_bullets_set)

        for answer in self.answers:
            self.text += '\n\n' + number_bullets_set[0] + ' ' + answer.text
            self.answers[self.answers.index(answer)].bullet = number_bullets_set[0]
            number_bullets_set.pop(0)


def get_randomized_question_list(chat_id: int) -> list:
    '''
    Возвращает перемешанный список question_id, набранный
    из всех сетов пользователя в нужных количествах.
    '''
    sets_list = pg.get_users_set_list(chat_id = chat_id)
    question_list = []

    for _set in sets_list:
        questions = pg.get_question_ids_by_set_id(_set[0])
        random.shuffle(questions)
        question_list.extend(questions[:_set[2]])

    return question_list
