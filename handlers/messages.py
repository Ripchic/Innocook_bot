from aiogram import Router, F
from aiogram.types import Message
from keyboards import reply, inline

router = Router()


# @router.message()
# async def echo(message: Message):
#     msg = message.text.lower()
#     if msg == "меню":
#         await message.answer("Choose action:", reply_markup=reply.main)
#     elif msg == "устройства":
#         user_id = message.from_user.id
#         data = inline.devices(user_id)
#         await message.answer(
#             f"Ваши устройства: {data[0]} шт. Выберите одно для взаимодействия:",
#             reply_markup=data[1])
#     else:
#         await message.answer(f"Unknown command: {message.text}")
