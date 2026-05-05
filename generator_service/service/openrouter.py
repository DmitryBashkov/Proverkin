# project
from config_data.config import config
from prompts.system import SYSTEM_TEXT

# misc
import json
import logging
import aiohttp

logger = logging.getLogger(__name__)


class OpenRouterClient:

    def __init__(self):
        self.api_key = config.openrouter.api_key
        self.base_url = config.openrouter.base_url.rstrip('/')
        self.default_model = config.openrouter.default_model
        self.referer = config.openrouter.referer
        self.title = config.openrouter.title

    async def generate_question(self, topic_prompt: str, model: str = None) -> dict | None:
        '''
        Возвращает dict вида:
            {"question": "...", "answers": [{"text": "...", "right": true}, ...]}
        либо None, если не удалось получить корректный JSON.
        '''
        if not self.api_key:
            logger.error('OPENROUTER_API_KEY не задан')
            return None

        model = model or self.default_model

        payload = {
            'model': model,
            'temperature': 0.8,
            'response_format': {'type': 'json_object'},
            'messages': [
                {'role': 'system', 'content': SYSTEM_TEXT},
                {'role': 'user', 'content': topic_prompt}
            ]
        }

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': self.referer,
            'X-Title': self.title
        }

        url = f'{self.base_url}/chat/completions'

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers = headers, json = payload, timeout = 120) as resp:
                    raw = await resp.text()
                    if resp.status >= 400:
                        logger.error(f'OpenRouter {resp.status}: {raw[:500]}')
                        return None
                    data = json.loads(raw)
        except Exception as e:
            logger.error(f'OpenRouter call failed: {e}')
            return None

        try:
            content = data['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            logger.error(f'OpenRouter unexpected response: {data} ({e})')
            return None

        # модель должна вернуть JSON, но на всякий случай аккуратно парсим
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # пытаемся выкусить { ... } из ответа
            start = content.find('{')
            end = content.rfind('}')
            if start == -1 or end == -1:
                logger.error(f'OpenRouter not a JSON: {content[:300]}')
                return None
            try:
                parsed = json.loads(content[start:end + 1])
            except json.JSONDecodeError as e:
                logger.error(f'OpenRouter cannot parse JSON: {e}, content={content[:300]}')
                return None

        # минимальная валидация
        if 'question' not in parsed or 'answers' not in parsed:
            logger.error(f'OpenRouter invalid schema: {parsed}')
            return None
        if not isinstance(parsed['answers'], list) or len(parsed['answers']) < 2:
            logger.error(f'OpenRouter not enough answers: {parsed}')
            return None
        right_count = sum(1 for a in parsed['answers'] if a.get('right'))
        if right_count != 1:
            logger.error(f'OpenRouter must have exactly 1 right answer: {parsed}')
            return None

        return parsed


openrouter_client = OpenRouterClient()
