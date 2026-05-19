# aiogram
import asyncio
from aiogram import Bot
from aiogram.types import BotCommand

# project
from config_data.config import config
from handlers import new_user_handlers, admin_handlers, stat_handlers, user_handlers, quiz_handlers
from utils.bot_dispatcher import dp
from service.quiz import schedule_quiz
from database.connector import SQLite3Connector as sqlite3_connector

# misc
import logging
from logging import handlers


'''
Configure logging.
Logs will be written to files, one file per day.
A new log file will be opened at midnight.
'''

logger = logging.getLogger()
logger.setLevel(logging.INFO)
log_format = f"%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
logHandler = handlers.TimedRotatingFileHandler('logs/qqb_bot.log', when='midnight', interval=1)
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(logging.Formatter(log_format))
logger.addHandler(logHandler)
logger.info('Proverkin Bot started')

# logging.basicConfig(level = logging.INFO)
# logger.info(f'Quick Quiz Bot 0.4 started')
bot: Bot = None
# Function to configure and start the bot

async def main():

    # Load config into the config variable
    # config: Config = load_config()
    
    # Initialize the bot and dispatcher
    bot: Bot = Bot(token = config.tg_bot.token)
    
    # storage: MemoryStorage = MemoryStorage()
    # dp: Dispatcher = Dispatcher(storage = storage)

    # Register routers in the dispatcher
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)
    dp.include_router(new_user_handlers.router)
    dp.include_router(stat_handlers.router)
    dp.include_router(quiz_handlers.router)

    # Create the list of commands and their descriptions for the menu button
    main_menu_commands = [
        BotCommand(
            command = '/quiz',
            description = 'Start a quiz right now'),
        BotCommand(
            command = '/restart',
            description = 'If something went wrong and you stopped receiving scheduled quizzes'),
    ]

    # setting commands for the bot
    await bot.set_my_commands(main_menu_commands)


    # checking database
    assert sqlite3_connector.init_check()

    total_users = sqlite3_connector.get_user_qty()
    total_scheduled_users = 0

    # Schedule quizzes for all active users
    for user in sqlite3_connector.get_all_active_users_with_chat_id():
        await schedule_quiz(bot, user[0], user[1], notify = False)
        total_scheduled_users += 1

    logging.info(f'Quizzes scheduled for {total_scheduled_users} out of {total_users} users')


    # Skip accumulated updates and start polling
    await bot.delete_webhook(drop_pending_updates = True)
    # await dp.startup.register(set_main_menu)
    await dp.start_polling(bot)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
