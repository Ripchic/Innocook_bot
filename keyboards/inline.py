# from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
#
#
# async def devices(user_id, db):
#     user_devices = await db.users.find_one({"_id": user_id})["devices"]
#     keyboard = [
#         [InlineKeyboardButton(text=f"{device}", callback_data=f"device_{device}") for device in user_devices],
#         [InlineKeyboardButton(text="Добавить устройство", callback_data="add_device"),
#          InlineKeyboardButton(text="Удалить устройство", callback_data="remove_device")],
#         [InlineKeyboardButton(text="Инструкция", callback_data="add_instruction"), ],
#     ]
#     return len(user_devices), InlineKeyboardMarkup(inline_keyboard=keyboard)
#
#
# device_control = InlineKeyboardMarkup(
#     inline_keyboard=[
#         [
#             InlineKeyboardButton(text="Старт", callback_data="on"),
#             InlineKeyboardButton(text="Стоп", callback_data="off"),
#         ],
#         [
#             InlineKeyboardButton(text="Установить температуру", callback_data="temperature"),
#         ],
#         [InlineKeyboardButton(text="Состояние", callback_data="status"),
#          ]
#     ],
# )
