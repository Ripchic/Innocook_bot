from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject, CommandStart

from keyboards import reply, builders

from motor.core import AgnosticDatabase as MDB

router = Router()


@router.message(Command("menu"))
@router.callback_query(F.data == "menu")
async def cmd_menu(message: Message | CallbackQuery):
    pattern = dict(
        text="Чтобы начать, выбери один из вариантов:",
        reply_markup=builders.inline_builder(
            ["Мои Устройства", "Мой user_id", "Контакты", "Помощь"],
            ["devices", "user_id", "contacts", "help"],
            [1, 1, 1])
    )
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(**pattern)
        await message.answer()  # let bot know that callback was handled
    else:
        await message.answer(**pattern)


# callback for main menu
@router.callback_query(F.data == "contacts")
async def cmd_contacts(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        text="Контакты для связи: (добавить кнопки со ссылками):\n", reply_markup=builders.inline_builder(
            ["<< Назад"], ["menu"], [1]
        ))
    await callback_query.answer()


@router.callback_query(F.data == "help")
async def cmd_help(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        text="Помощь по использованию бота: (добавить, что нужно)\n", reply_markup=builders.inline_builder(
            ["<< Назад"], ["menu"], [1]
        )
    )
    await callback_query.answer()


@router.callback_query(F.data == "user_id")
async def cmd_user_id(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        text=f"Ваш user_id: {callback_query.from_user.id}\n", reply_markup=builders.inline_builder(
            ["<< Назад"], ["menu"], [1]
        )
    )
    await callback_query.answer()


@router.message(CommandStart())
async def cmd_start(message: Message, db: MDB):
    await message.answer(f"Привет, я оффициальный бот InnoCook!. 👋\n"
                         f"Я умею управлять сувидами InnoCook послених ревизий. 🤖\n"
                         f"Начиная использование телеграм-бота, вы соглашаетесь с правилами пользования, ознакомиться с которыми можно здесь: /rules")
    await cmd_menu(message)
    user_id = message.from_user.id
    user = await db.users.find_one({"_id": user_id})
    if user:
        return
    await db.users.insert_one({
        "_id": user_id,
        "devices": [],
        "presets": []
    })
    await message.answr()


@router.message(Command("user_id"))
async def cmd_user_id(message: Message):
    await message.answer(f"{message.from_user.id}")
