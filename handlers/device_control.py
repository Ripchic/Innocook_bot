from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.states import DeviceControl
from keyboards.builders import inline_builder
from mqtt import publish
from utils.states import DeviceManagement
from motor.core import AgnosticDatabase as MDB

router = Router()


def device_status_text(device_name: str, status: str, temperature: str, timer: str, duration: str):
    return f"Для обновления информации нажмите на кнопку 'Состояние'\n\n" \
           f"Устройство: '{device_name}':\n" \
           f"Состояние:{status}\n" \
           f"Температура: {temperature}\n" \
           f"Таймер: {timer}\n"


async def update_device_status(callback_query: CallbackQuery, device_name: str, device_id: int, status: str,
                               temperature: str,
                               timer: str, duration: str):
    await callback_query.message.edit_text(
        device_status_text(device_name, status, temperature, timer, duration),
        reply_markup=inline_builder(
            ["Старт", "Стоп", "Мои пресеты", "Состояние", "Изменить имя", "<< Назад", "Удалить"],
            [f"{val}_{device_id}" for val in
             ["on", "off", "presets", "status", "editDeviceName", "devices", "removeDevice"]],
            [2, 1, 1, 1, 2]
        )
    )


# action_<pressed button index>
@router.callback_query(F.data.startswith("device_"))
async def device_control(callback_query: CallbackQuery, state: FSMContext, db: MDB):
    await state.clear()  # clear the state if callback from back button
    button_id = int(callback_query.data.split('_')[1])
    user_id = callback_query.from_user.id
    user = await db.users.find_one({"_id": user_id})
    user_devices = user["devices"]
    device = user_devices[button_id]
    device_id = device["device_id"]
    device_name = device["name"]
    await update_device_status(callback_query, device_name, button_id, "Устарело", "Устарело", "Устарело", "Устарело")
    await callback_query.answer()


@router.callback_query(F.data.startswith("on_"))
async def device_on(callback_query: CallbackQuery, mqtt_client, db: MDB):
    button_id = int(callback_query.data.split('_')[1])
    user = await db.users.find_one({"_id": callback_query.from_user.id})
    user_devices = user["devices"]
    device = user_devices[button_id]
    device_name = device["name"]
    device_id = device["device_id"]
    status = "Включено"
    temperature = timer = duration = "Значение с сувида"
    if callback_query.message.text != device_status_text(device_name, status, temperature, timer, duration):
        await update_device_status(callback_query, device_name, button_id, status, temperature, timer, duration)
        await publish.set_power(mqtt_client, callback_query.from_user.id, device_id, "on")
    else:
        await callback_query.message.answer(f"Устройство '{device_name}' уже включено.", reply_markup=inline_builder(
            ["<< Назад"],
            ["delete"],
            [1]))


@router.callback_query(F.data.startswith("off_"))
async def device_off(callback_query: CallbackQuery, mqtt_client, db: MDB):
    button_id = int(callback_query.data.split('_')[1])
    user = await db.users.find_one({"_id": callback_query.from_user.id})
    user_devices = user["devices"]
    device = user_devices[button_id]
    device_name = device["name"]
    device_id = device["device_id"]
    status = "Выключено"
    temperature = timer = duration = "Значение с сувида"
    if callback_query.message.text != device_status_text(device_name, status, temperature, timer, duration):
        await update_device_status(callback_query, device_name, button_id, status, temperature, timer, duration)
        await publish.set_power(mqtt_client, callback_query.from_user.id, device_id, "off")
    else:
        await callback_query.message.answer(f"Устройство '{device_name}' и так не работает.",
                                            reply_markup=inline_builder(
                                                ["<< Назад"],
                                                ["delete"],
                                                [1]))


@router.callback_query(F.data.startswith("status_"))
async def device_status(callback_query: CallbackQuery, mqtt_client, db: MDB):
    button_id = int(callback_query.data.split('_')[1])
    user = await db.users.find_one({"_id": callback_query.from_user.id})
    user_devices = user["devices"]
    device = user_devices[button_id]
    device_name = device["name"]
    device_id = device["device_id"]
    status = "Статус с сувида"
    temperature = timer = duration = "Значение с сувида"
    await update_device_status(callback_query, device_name, button_id, status, temperature, timer, duration)
    await publish.get_status(mqtt_client, callback_query.from_user.id, device_id)


@router.callback_query(F.data.startswith("editDeviceName"))
async def edit_device_name(callback_query: CallbackQuery, state: FSMContext):
    button_id = int(callback_query.data.split('_')[1])
    await state.update_data(button_id=button_id)
    await callback_query.message.edit_text("Введите новое имя устройства:")
    await state.set_state(DeviceManagement.edit_device_name)
    await callback_query.answer()


@router.message(DeviceManagement.edit_device_name)
async def set_device_name(message: Message, state: FSMContext, db: MDB):
    new_name = message.text
    await state.update_data(edit_device_name=new_name)
    user_id = message.from_user.id
    data = await state.get_data()
    button_id = data["button_id"]
    await db.users.update_one({"_id": user_id},
                              {"$set": {f"devices.{button_id}.name": new_name}})
    await state.clear()
    await message.answer(f"Имя устройства успешно изменено на '{new_name}'.", reply_markup=inline_builder(
        ["К списку устройств"],
        ["devices"],
        [1]
    ))


@router.callback_query(F.data.startswith("removeDevice"))
async def remove_device(callback_query: CallbackQuery, db: MDB):
    button_id = int(callback_query.data.split('_')[1])
    user_id = callback_query.from_user.id
    user = await db.users.find_one({"_id": user_id})
    user_devices = user["devices"]
    device = user_devices[button_id]
    device_name = device["name"]
    device_id = device["device_id"]
    await db.users.update_one({"_id": user_id}, {"$pull": {"devices": {"device_id": device_id}}})
    await callback_query.message.answer(f"Устройство '{device_name}' успешно удалено.", reply_markup=inline_builder(
        ["<< Назад"],
        ["devices"],
        [1]
    ))
