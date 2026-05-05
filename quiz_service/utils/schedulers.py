# apscheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# misc
import logging

logger = logging.getLogger(__name__)

quiz_scheduler = AsyncIOScheduler(
    job_defaults = {'misfire_grace_time': 60 * 60}
)
