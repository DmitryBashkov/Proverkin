# project
from database.connector import SQLite3Connector as sqlite3_connector

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

    def __init__(self, question_id: int, question_text: str, question_type: str, shuffle: bool = True):

        self.id = question_id
        self.text = question_text
        self.question_type = question_type

        self.answers = []
        for answer in sqlite3_connector.get_answers(question_id):
            self.answers.append(Answer(
                id_ = answer[0],
                text = answer[1],
                right = bool(answer[2],),
                bullet = ''
            ))

        if shuffle:
            random.shuffle(self.answers)

        '''
        проверяем, есть ли среди ответов длинные строки
        если есть, то засовываем их в сам текст вопроса,
        а в ответах просто даем цифры
        '''

        self.long_asnwers = False

        if shuffle:
            for answer in self.answers:
                if len(answer.text) > 35:
                    self._shorten_question()
                    self.long_asnwers = True
                    break

    def _shorten_question(self):
        # number_bullets_set = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']

        number_bullets_set = ['🐶', '🐱', '🐸', '🦄', '🐥', '🐌', '🐻', '🐼', '🐷']
        
        random.shuffle(number_bullets_set)
        # random.shuffle(self.answers)
        
        for answer in self.answers:
            self.text += '\n\n' + number_bullets_set[0] + ' ' + answer.text
            self.answers[self.answers.index(answer)].bullet = number_bullets_set[0]
            
            number_bullets_set.pop(0)

    def _form_row(self) -> list:
        row = []

        row.append(self.id)
        row.append(self.text)

        self.answers.sort(reverse = True, key = lambda answer: answer.right)
        right_answer_count = 0
        for answer in self.answers: 
            if answer.right: right_answer_count += 1
            row.append(answer.id_)
            row.append(answer.text)

        row.insert(2, right_answer_count)

        return row

class QuestionSet():

    def __init__(self, set_id: int = None, set_name: str = None, need_questions = True):
        self.set_id = set_id
        self.set_name = set_name
        self.questions = []

        # need_question param need for form question list
        if need_questions:
            for q in sqlite3_connector.get_questions(set_id = set_id):
                self.questions.append(
                    Question(
                        question_id = q[0],
                        questions_text = q[1],
                        question_type = q[2]
                    )
                )

    def __eq__(self, item):
        if item == self.set_id:
            return True
        return False