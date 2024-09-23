# project
from messages.messages import *
from utils.schedulers import quiz_scheduler

#misc
import datetime
import random
import pytz
import logging
from apscheduler.job import Job
import pytz

logger = logging.getLogger(__name__)

def get_new_time(period: int = 1, delta: int = 1, is_test = False):
    
    if is_test == False:
        now = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
        if now.hour >= 10:
            date = now + datetime.timedelta(days=1)
            return date.replace(hour = 10, minute = random.randint(0,59))
        else:
            return now.replace(hour = 10, minute = random.randint(0,59))
        
    else: 
        now = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
        return now + datetime.timedelta(seconds = random.randrange(period, period + delta))

def get_job(name: str) -> Job:
    for job in quiz_scheduler.get_jobs():
        if job.name == name: return job
    return None

def drop_at(username: str) -> str:
    return username.replace('@', '')

def replace_space(str_: str) -> str:
    return str_.replace(' ', '_')