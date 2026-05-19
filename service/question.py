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

    def __init__(self, question_id: int, for_quiz: bool = True):

        self.id = question_id
        
        self.thesis = None
        self.text = sqlite3_connector.get_question_text(question_id)

        self.answers = []
        for answer in sqlite3_connector.get_answers(question_id):
            self.answers.append(Answer(
                id_ = answer[0],
                text = answer[1],
                right = bool(answer[2],),
                bullet = ''
            ))

        if for_quiz:
            random.shuffle(self.answers)

        '''
        Check if any answers contain long strings.
        If so, embed them in the question text itself,
        and use only numbers/bullets in the answer buttons.
        '''

        self.long_asnwers = False

        if for_quiz:
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

    def __init__(self, set_id: int):

        self.questions = []

        for question_id in sqlite3_connector.get_question_ids_by_set_id(set_id):
            self.questions.append(Question(question_id, False))


    pass
