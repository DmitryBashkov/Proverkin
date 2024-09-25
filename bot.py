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
конфигурируем логирование
логи будут писаться в файлы, каждый новый день -- отдельный файл
новый файл с логами будет открываться в полночь
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
# Функция конфигурирования и запуска бота

async def main():

    # Загружаем конфиг в переменную config
    # config: Config = load_config()
    
    # Инициализируем бот и диспетчер
    bot: Bot = Bot(token = config.tg_bot.token)
    
    # storage: MemoryStorage = MemoryStorage()
    # dp: Dispatcher = Dispatcher(storage = storage)

    # Регистриуем роутеры в диспетчере
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)
    dp.include_router(new_user_handlers.router)
    dp.include_router(stat_handlers.router)
    dp.include_router(quiz_handlers.router)

    # Создаем список с командами и их описанием для кнопки menu
    main_menu_commands = [
        BotCommand(
            command = '/quiz',
            description = 'Запустить квиз прямо сейчас'),
        BotCommand(
            command = '/restart',
            description = 'Если что-то пошло не так и вы перестали получать запланированные квизы'),
    ]

    # setting commands for the bot
    await bot.set_my_commands(main_menu_commands)


    # checking database
    assert sqlite3_connector.init_check()

    total_users = sqlite3_connector.get_user_qty()
    total_scheduled_users = 0

    # запускаем проверку на наличие квиза для все пользователей
    for user in sqlite3_connector.get_all_active_users_with_chat_id():
        await schedule_quiz(bot, user[0], user[1], notify = False)
        total_scheduled_users += 1

    logging.info(f'Запланированы квизы для {total_scheduled_users} из {total_users} пользователей')


    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates = True)
    # await dp.startup.register(set_main_menu)
    await dp.start_polling(bot)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()