from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from utils.states import DeviceManagement
from keyboards import builders

from motor.core import AgnosticDatabase as MDB

from paho.mqtt.client import Client

router = Router()


@router.callback_query(F.data.startswith("devices"))
async def show_devices(callback_query: CallbackQuery, state: FSMContext, db: MDB):
    await state.clear()  # clear state if callback from back button
    user_id = callback_query.from_user.id
    user = await db.users.find_one({"_id": user_id})
    user_devices = user["devices"]
    devices_names = [device["name"] for device in user_devices]
    await callback_query.message.edit_text(
        f"Ваши устройства: {len(user_devices)} шт. Выберите взаимодействия:",
        reply_markup=builders.inline_builder(
            [*devices_names, "Добавить устройство ", "Удалить устройство ", "<< Назад", "Инструкция"],
            [f"device_{i}" for i, _ in enumerate(user_devices)] +
            ["add_device", "remove_device", "menu", "add_instruction"],
            [1 for _ in range(len(user_devices))] + [2, 2]
        )
    )
    await callback_query.answer()


@router.callback_query(F.data == "remove_device")
async def remove_device(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("Введите имя устройства для удаления:", reply_markup=builders.inline_builder(
        ["<< Назад"],
        ["devices"],
        [1]
    ))
    await state.set_state(DeviceManagement.remove_name)
    await callback_query.answer()


@router.message(DeviceManagement.remove_name)
async def remove_device_name(message: Message, state: FSMContext, db: MDB):
    device_name = message.text
    user_id = message.from_user.id
    user = await db.users.find_one({"_id": user_id})
    user_devices = user["devices"]
    if device_name not in user_devices:
        await message.answer(
            f"Устройство с именем '{device_name}' не найдено.\nПроверьте имя вашего устройства или повторите ввод.",
            reply_markup=builders.inline_builder(
                ["Мои устройства"],
                ["devices"],
                [1]
            ))
    else:
        db.users.update_one({"_id": user_id}, {"$pull": {"devices": device_name}})
        await state.clear()
        await message.answer("Устройство успешно удалено", reply_markup=builders.inline_builder(
            ["Мои устройства"],
            ["devices"],
            [1]
        ))


@router.callback_query(F.data == "add_instruction")
async def cb_device_managemt_instruction(callback_query: CallbackQuery):
    await callback_query.message.answer("Сюда добавить инструкцию по сопряжению", reply_markup=builders.inline_builder(
        ["Понятно"],
        ["delete"],
        [1]
    ))


@router.callback_query(F.data == "delete")
async def cb_device_managemt_instruction(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
