import requests
import json
from config_data.config import config
from datetime import datetime

system_text = \
    '''
    You are a test developer for checking students' knowledge. 
    You have written an excellent test for a company, but it has been in use for a long time.
    Because of this, students have gotten used to the questions and can answer without reading them fully: it is enough for them to see a few keywords in the right places to know exactly which question it is and what answer they need to give.
    To prevent this, you need to rephrase the question.
    You can rearrange or add words, replace them with synonyms, but your changes must not alter the meaning of the question.
    Keep in mind that some words must remain unchanged, as they may be specific terms from a particular industry or company.
    Your response must contain only the question and only one version of it in plain text format without any text formatting (no asterisks for bold text).
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
