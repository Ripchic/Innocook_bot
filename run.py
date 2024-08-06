import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import commands, messages, device_management, device_control, presets
from mqtt import setup
from dotenv import load_dotenv

from motor.motor_asyncio import AsyncIOMotorClient


async def init_bot():
    bot = Bot(token=os.getenv("BOT_TOKEN"),
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    return bot, dp


async def main():
    load_dotenv()  # add .env file to the project root
    bot, dp = await init_bot()
    cluster = AsyncIOMotorClient(host="localhost", port=27017)
    db = cluster.Innocook

    mqtt_client = setup.connect_mqtt(db, bot)

    # Include used routers in correct order
    dp.include_routers(
        commands.router,
        device_management.router,
        device_control.router,
        presets.router,
        messages.router,

    )
    await bot.delete_webhook(drop_pending_updates=True)  # Drop previous commands
    # could be used to set commands for private chats only
    # await bot.set_my_commands(commands=[], scope=types.BotCommandScopeAllPrivateChats())
    # can pass kwargs to any handler, in this case mqtt_client and database
    await dp.start_polling(bot, mqtt_client=mqtt_client, db=db)


if __name__ == "__main__":
    asyncio.run(main())
