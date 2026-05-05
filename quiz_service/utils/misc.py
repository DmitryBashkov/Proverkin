# project
from utils.schedulers import quiz_scheduler
from config_data.config import config

# misc
import datetime
import random
import pytz
import logging
from apscheduler.job import Job

logger = logging.getLogger(__name__)


def get_new_time(period: int = 1, delta: int = 1, is_test: bool = False):
    '''
    Возвращает datetime, в который должен сработать следующий квиз.
    Если сейчас раньше quiz_start_hour -- сегодня в этот час;
    если уже позже -- завтра.
    '''
    if not is_test:
        now = datetime.datetime.now(pytz.timezone(config.quiz.timezone))
        start_h = config.quiz.quiz_start_hour
        if now.hour >= start_h:
            date = now + datetime.timedelta(days = 1)
            return date.replace(hour = start_h, minute = random.randint(0, 59),
                                second = 0, microsecond = 0)
        return now.replace(hour = start_h, minute = random.randint(0, 59),
                           second = 0, microsecond = 0)

    now = datetime.datetime.now(pytz.timezone(config.quiz.timezone))
    return now + datetime.timedelta(seconds = random.randrange(period, period + delta))


def get_job(name: str) -> Job:
    for job in quiz_scheduler.get_jobs():
        if job.name == name:
            return job
    return None
