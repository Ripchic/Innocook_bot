from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.states import PresetsManagement
from keyboards.builders import inline_builder
from aiogram.filters.callback_data import CallbackData

from mqtt import publish

from motor.core import AgnosticDatabase as MDB

router = Router()


@router.callback_query(F.data.startswith("presets_"))
async def device_on(callback_query: CallbackQuery, db: MDB, state: FSMContext):
    button_id = int(callback_query.data.split('_')[1])
    user_id = callback_query.from_user.id
    user = await db.users.find_one({"_id": user_id})
    user_presets = user["presets"]

    # preset_presetID_deviceID
    await callback_query.message.edit_text(f"Ваши пресеты: {len(user_presets)} шт.", reply_markup=inline_builder(
        text=[f"Имя: {preset["name"]}; Темп: {preset["temp"]}; Таймер: {preset["timer"]}" for preset in
              user_presets] + [
                 "Добавить пресет", "<< Назад"],
        callback_data=[f"preset_{i}_{button_id}" for i, _ in enumerate(user_presets)] + [f"add_preset_{button_id}",
                                                                                         f"device_{button_id}"],
        sizes=[1 for _ in range(len(user_presets) + 2)]
    ))
    await callback_query.answer()


@router.callback_query(F.data.startswith("preset_"))
async def device_on(callback_query: CallbackQuery, db: MDB):
    user_id = callback_query.from_user.id
    user = await db.users.find_one({"_id": user_id})
    preset_id = int(callback_query.data.split('_')[1])
    device_id = int(callback_query.data.split('_')[2])
    user_presets = user["presets"]
    preset = user_presets[preset_id]
    await callback_query.message.edit_text(f"Название пресета: '{preset["name"]}':", reply_markup=inline_builder(
        text=["Установить", "Редактировать", "<< Назад", "Удалить"],
        callback_data=[f"run_preset_{preset_id}_{device_id}", f"editPreset_{preset_id}_{device_id}",
                       f"presets_{device_id}",
                       f"delete_preset_{preset_id}_{device_id}"],
        sizes=[1, 1, 2]
    ))


@router.callback_query(F.data.startswith("delete_preset"))
async def delete_preset(callback_query: CallbackQuery, db: MDB):
    preset_id = int(callback_query.data.split('_', -1)[2])
    device_id = int(callback_query.data.split('_', -1)[3])
    user_id = callback_query.from_user.id
    await db.users.update_one({"_id": user_id},
                              {"$unset": {f"presets.{preset_id}": ""}})
    await db.users.update_one({"_id": user_id},
                              {"$pull": {"presets": None}})

    await callback_query.message.edit_text("Пресет успешно удалён", reply_markup=inline_builder(
        text=["<< Назад"],
        callback_data=[f"presets_{device_id}"],
        sizes=[1]
    ))
    await callback_query.answer()


@router.callback_query(F.data.startswith("add_preset"))
async def add_preset(callback_query: CallbackQuery, state: FSMContext, db: MDB):
    device_id = int(callback_query.data.split('_')[2])
    await state.update_data(device_id=device_id)
    await callback_query.message.edit_text("Введите имя нового пресета:", reply_markup=inline_builder(
        text=["<< Назад"],
        callback_data=[f"presets_{device_id}"],
        sizes=[1]
    ))
    await state.set_state(PresetsManagement.name)
    await callback_query.answer()


@router.message(PresetsManagement.name)
async def add_preset_name(message: Message, state: FSMContext):
    preset_name = message.text

    await state.update_data(name=preset_name)
    await state.set_state(PresetsManagement.temp)
    await message.answer("Введите температуру для пресета в формате 12 или 12.3:")


@router.message(PresetsManagement.temp, F.text.regexp(r'^-?\d+(\.\d+)?$|^-?\d+,\d+$'))
async def add_preset_temp(message: Message, state: FSMContext, db: MDB):
    preset_temp = message.text

    await state.update_data(temp=preset_temp)
    await state.set_state(PresetsManagement.timer)
    await message.answer("Введите таймер пресета в формате чч или чч.мм:")


@router.message(PresetsManagement.temp)
async def add_preset_temp(message: Message):
    print(message.text)
    await message.answer("Температура должна быть числом в формате 12 или 12.3\nВведите число еще раз.")


@router.message(PresetsManagement.timer, F.text.regexp(r'^-?\d+(\.\d+)?$|^-?\d+,\d+$'))
async def add_preset_timer(message: Message, state: FSMContext, db: MDB):
    timer = message.text
    data = await state.get_data()
    user_id = message.from_user.id
    name = data["name"]
    temp = data["temp"]
    new_preset = {
        "name": name,
        "temp": temp,
        "timer": timer
    }
    await db.users.update_one({"_id": user_id},
                              {"$push": {"presets": new_preset}})
    data = await state.get_data()
    device_id = data["device_id"]
    await message.answer("Пресет успешно добавлен.", reply_markup=inline_builder(
        text=["<< Назад"],
        callback_data=[f"presets_{device_id}"],
        sizes=[1]
    ))


@router.message(PresetsManagement.timer)
async def add_preset_timer(message: Message):
    await message.answer("Таймер должен быть числом в формате чч или чч.мм\nВведите число ещё раз:")


@router.callback_query(F.data.startswith("edit_name_"))
async def edit_preset_name(callback_query: CallbackQuery, state: FSMContext):
    preset_id = int(callback_query.data.split('_', -1)[2])
    device_id = int(callback_query.data.split('_', -1)[3])
    await state.update_data(preset_id=preset_id)
    await state.update_data(device_id=device_id)
    await state.set_state(PresetsManagement.edit_name)
    await callback_query.message.edit_text("Введите новое имя пресета:")
    await callback_query.answer()


@router.message(PresetsManagement.edit_name)
async def edit_preset_name(message: Message, state: FSMContext, db: MDB):
    preset_id = (await state.get_data())["preset_id"]
    device_id = (await state.get_data())["device_id"]
    new_name = message.text
    user_id = message.from_user.id
    await db.users.update_one({"_id": user_id},
                              {"$set": {f"presets.{preset_id}.name": new_name}})
    await message.answer("Имя пресета успешно изменено.", reply_markup=inline_builder(
        text=["<< Назад"],
        callback_data=[f"presets_{device_id}"],
        sizes=[1]
    ))
    await state.clear()


@router.callback_query(F.data.startswith("edit_temp_"))
async def edit_preset_temp(callback_query: CallbackQuery, state: FSMContext):
    preset_id = int(callback_query.data.split('_', -1)[2])
    device_id = int(callback_query.data.split('_', -1)[3])
    await state.update_data(preset_id=preset_id)
    await state.update_data(device_id=device_id)
    await state.set_state(PresetsManagement.edit_temp)
    await callback_query.message.edit_text("Введите новую температуру пресета:")
    await callback_query.answer()


@router.message(PresetsManagement.edit_temp, F.text.regexp(r'^-?\d+(\.\d+)?$|^-?\d+,\d+$'))
async def edit_preset_temp(message: Message, state: FSMContext, db: MDB):
    preset_id = (await state.get_data())["preset_id"]
    device_id = (await state.get_data())["device_id"]
    new_temp = message.text
    user_id = message.from_user.id
    await db.users.update_one({"_id": user_id},
                              {"$set": {f"presets.{preset_id}.temp": new_temp}})
    await message.answer("Температура пресета успешно изменена.", reply_markup=inline_builder(
        text=["<< Назад"],
        callback_data=[f"presets_{device_id}"],
        sizes=[1]
    ))
    await state.clear()


@router.message(PresetsManagement.edit_temp)
async def edit_preset_temp(message: Message):
    await message.answer("Температура должна быть числом в формате 12 или 12.3 \nВведите число еще раз.")


@router.callback_query(F.data.startswith("edit_timer_"))
async def edit_preset_timer(callback_query: CallbackQuery, state: FSMContext):
    preset_id = int(callback_query.data.split('_', -1)[2])
    device_id = int(callback_query.data.split('_', -1)[3])
    await state.update_data(preset_id=preset_id)
    await state.update_data(device_id=device_id)
    await state.set_state(PresetsManagement.edit_timer)
    await callback_query.message.edit_text("Введите новый таймер пресета в формате чч.мм:")
    await callback_query.answer()


@router.message(PresetsManagement.edit_timer, F.text.regexp(r'^-?\d+(\.\d+)?$|^-?\d+,\d+$'))
async def edit_preset_timer(message: Message, state: FSMContext, db: MDB):
    preset_id = (await state.get_data())["preset_id"]
    device_id = (await state.get_data())["device_id"]
    new_timer = message.text
    user_id = message.from_user.id
    await db.users.update_one({"_id": user_id},
                              {"$set": {f"presets.{preset_id}.timer": new_timer}})
    await message.answer("Таймер пресета успешно изменен.", reply_markup=inline_builder(
        text=["<< Назад"],
        callback_data=[f"presets_{device_id}"],
        sizes=[1]
    ))
    await state.clear()


@router.message(PresetsManagement.edit_timer)
async def edit_preset_timer(message: Message):
    await message.answer("Таймер должен быть числом \nВведите число еще раз в формате чч.мм:")


@router.callback_query(F.data.startswith("editPreset_"))
async def edit_preset(callback_query: CallbackQuery):
    preset_id = int(callback_query.data.split('_', -1)[1])
    device_id = int(callback_query.data.split('_', -1)[2])
    await callback_query.message.edit_text("Выберите что вы хотите изменить:", reply_markup=inline_builder(
        text=["Имя", "Температура", "Таймер", "<< Назад"],
        callback_data=[f"edit_name_{preset_id}_{device_id}", f"edit_temp_{preset_id}_{device_id}",
                       f"edit_timer_{preset_id}_{device_id}",
                       f"presets_{device_id}"],
        sizes=[1, 1, 1, 1]
    ))
    await callback_query.answer()


@router.callback_query(F.data.startswith("run_preset_"))
async def run_preset(callback_query: CallbackQuery, db: MDB, mqtt_client):
    preset_id = int(callback_query.data.split('_', -1)[2])
    button_id = int(callback_query.data.split('_', -1)[3])
    user_id = callback_query.from_user.id
    user = await db.users.find_one({"_id": user_id})
    user_devices = user["devices"]
    device = user_devices[button_id]
    device_id = device["device_id"]
    user_presets = user["presets"]
    preset = user_presets[preset_id]

    await publish.set_preset(mqtt_client, user_id, device_id, preset)
    await callback_query.message.edit_text("Пресет установлен.", reply_markup=inline_builder(
        text=["<< Назад к устройству"],
        callback_data=[f"device_{button_id}"],
        sizes=[1]))
    await callback_query.answer()
