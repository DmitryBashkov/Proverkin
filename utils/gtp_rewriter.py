import requests
import json
from config_data.config import config
from datetime import datetime

system_text = \
    '''
    Ты разработчик тестов для проверки знаний студентов. 
    Ты составил отличный тест для компании, но он в работе уже продолжительное время.
    Из-за этого студенты привыкли к этим вопросам и могут ответить на него, не читая его полностью: им достаточно увидеть несколько ключевых слов в нужных местах, чтобы понять, что какой именно это вопрос и какой на него нужно дать ответ.
    Чтобы такого не происходило, тебе нужно перефразировать этот вопрос.
    Ты можешь переставлять или добавлять слова, менять их на синонимы, но твои изменения не должны менять смысл вопроса. 
    Имей в виду, что некоторые слова должны оставаться такими же, тк они могут быть специфичными терминами из конкретной индустрии или компании.
    Твой ответ должен содержать только вопрос и только в одном экземпляре в фомрате plain text без форматирования текста (без звездочек для выделения текста жирным)
    '''

def rewrite(question: str):
    prompt = {
        "completionOptions": {
            "maxTokens": 500,
            "stream": False,
            "temperature": 0.7
        },
        "messages": [
            {
            "role": "system",
            "text": system_text
            },
            {
            "role": "user",
            "text": question
            }
        ],
        "modelUri": "gpt://b1g6b7fogrgj9t5ick5v/yandexgpt-lite"
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {config.yandex_gpt_api}"
    }

    response = requests.post(url, headers = headers, json = prompt)
    result = response.text

    response_dict = json.loads(result)

    result = {
        "request": prompt['messages'], 
        "response": f'{response_dict["result"]["alternatives"][0]["message"]["text"]}'
    }

    return result