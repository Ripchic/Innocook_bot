from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.states import DeviceControl
from keyboards.builders import inline_builder
# from mqtt.mqtt_setup import publish_message
from mqtt import publish

from motor.core import AgnosticDatabase as MDB

router = Router()


def device_status_text(device_name: str, status: str, temperature: str, timer: str, duration: str):
    return f"Для обновления информации нажмите на кнопку 'Состояние'\n\n" \
           f"Устройство: '{device_name}':\n" \
           f"Состояние:{status}\n" \
           f"Температура: {temperature}\n" \
           f"Таймер: {timer}\n" \
           f"Время с последнего запуска: {duration}"


async def update_device_status(callback_query: CallbackQuery, device_name: str, device_id: int, status: str,
                               temperature: str,
                               timer: str, duration: str):
    await callback_query.message.edit_text(
        device_status_text(device_name, status, temperature, timer, duration),
        reply_markup=inline_builder(
            ["Старт", "Стоп", "Мои пресеты", "Температура", "Таймер", "<< Назад", "Состояние"],
            [f"{val}_{device_id}" for val in
             ["on", "off", "presets", "temperature", "timer", "devices", "status"]],
            [2, 1, 2, 2]
        )
    )


@router.callback_query(F.data.startswith("device_"))
async def device_control(callback_query: CallbackQuery, state: FSMContext, db: MDB):
    await state.clear()  # clear the state if callback from back button
    device_id = int(callback_query.data.split('_')[1])
    user_id = callback_query.from_user.id
    user = await db.users.find_one({"_id": user_id})
    user_devices = user["devices"]
    device_name = user_devices[device_id]
    await update_device_status(callback_query, device_name, device_id, "Устарело", "Устарело", "Устарело", "Устарело")
    await callback_query.answer()


@router.callback_query(F.data.startswith("on_"))
async def device_on(callback_query: CallbackQuery, mqtt_client, db: MDB):
    device_id = int(callback_query.data.split('_')[1])
    user = await db.users.find_one({"_id": callback_query.from_user.id})
    user_devices = user["devices"]
    device_name = user_devices[device_id]
    status = "Включено"
    temperature = timer = duration = "Значение с сувида"
    if callback_query.message.text != device_status_text(device_name, status, temperature, timer, duration):
        await update_device_status(callback_query, device_name, device_id, status, temperature, timer, duration)
        # await publish_message(mqtt_client, callback_query.from_user.id, device_name, "on")
        await publish.set_power(mqtt_client, callback_query.from_user.id, device_name, "on")
    else:
        await callback_query.message.answer(f"Устройство '{device_name}' уже включено.", reply_markup=inline_builder(
            ["<< Назад"],
            ["delete"],
            [1]))


@router.callback_query(F.data.startswith("off_"))
async def device_off(callback_query: CallbackQuery, mqtt_client, db: MDB):
    device_id = int(callback_query.data.split('_')[1])
    user = await db.users.find_one({"_id": callback_query.from_user.id})
    user_devices = user["devices"]
    device_name = user_devices[device_id]
    status = "Выключено"
    temperature = timer = duration = "Значение с сувида"
    if callback_query.message.text != device_status_text(device_name, status, temperature, timer, duration):
        await update_device_status(callback_query, device_name, device_id, status, temperature, timer, duration)
        # await publish_message(mqtt_client, callback_query.from_user.id, device_name, "off")
        await publish.set_power(mqtt_client, callback_query.from_user.id, device_name, "off")
    else:
        await callback_query.message.answer(f"Устройство '{device_name}' и так не работает.",
                                            reply_markup=inline_builder(
                                                ["<< Назад"],
                                                ["delete"],
                                                [1]))


@router.callback_query(F.data.startswith("status_"))
async def device_status(callback_query: CallbackQuery, mqtt_client, db: MDB):
    device_id = int(callback_query.data.split('_')[1])
    user = await db.users.find_one({"_id": callback_query.from_user.id})
    user_devices = user["devices"]
    device_name = user_devices[device_id]
    status = "Статус с сувида"
    temperature = timer = duration = "Значение с сувида"
    await update_device_status(callback_query, device_name, device_id, status, temperature, timer, duration)
    # await publish_message(mqtt_client, callback_query.from_user.id, device_name, "status")
    await publish.get_status(mqtt_client, callback_query.from_user.id, device_name)


@router.callback_query(F.data.startswith("temperature_"))
async def cb_add_device(callback_query: CallbackQuery, state: FSMContext, db: MDB):
    device_id = int(callback_query.data.split('_')[1])
    user = await db.users.find_one({"_id": callback_query.from_user.id})
    user_devices = user["devices"]
    device_name = user_devices[device_id]
    await callback_query.message.delete()
    await callback_query.message.answer(f"Введите требуемую температуру для '{device_name}'",
                                        reply_markup=inline_builder(
                                            ["<< Назад"], [f"device_{device_id}"], [1]
                                        ))
    await state.set_state(DeviceControl.temperature)
    await state.update_data(device_id=device_id)


#  regex for checking if the input is a number
@router.message(DeviceControl.temperature, F.text.regexp(r'^-?\d+(\.\d+)?$|^-?\d+,\d+$'))
async def set_temperature(message: Message, state: FSMContext, mqtt_client):
    temperature = message.text
    data = await state.get_data()
    device_id = data['device_id']
    user_id = message.from_user.id
    # await publish_message(mqtt_client, user_id, device_id, f"temp:{temperature}")
    await publish.set_temperature(mqtt_client, user_id, device_id, temperature)
    await state.clear()
    await message.answer("Температура успешно задана.", reply_markup=inline_builder(
        ["<< Назад"],
        [f"device_{device_id}"],
        [1]
    ))


# if the input is not a number
@router.message(DeviceControl.temperature)
async def set_temperature(message: Message, state: FSMContext):
    data = await state.get_data()
    device_id = data['device_id']
    await message.answer("Температура должна быть числом \nВведите число еще раз.", reply_markup=inline_builder(
        ["<< Назад"],
        [f"device_{device_id}"],
        [1]))


@router.callback_query(F.data.startswith("timer_"))
async def cb_add_device(callback_query: CallbackQuery, state: FSMContext, db: MDB):
    device_id = int(callback_query.data.split('_', 1)[1])
    user = await db.users.find_one({"_id": callback_query.from_user.id})
    user_devices = user["devices"]
    device_name = user_devices[device_id]
    await callback_query.message.delete()
    await callback_query.message.answer(f"Введите время работы '{device_name}' в формате 'часы.минуты'",
                                        reply_markup=inline_builder(
                                            ["<< Назад"], [f"device_{device_id}"], [1]
                                        ))
    await state.set_state(DeviceControl.timer)
    await state.update_data(device_id=device_id)


@router.message(DeviceControl.timer, F.text.regexp(r'^-?\d+(\.\d+)?$|^-?\d+,\d+$'))
async def set_timer(message: Message, state: FSMContext, mqtt_client):
    timer = message.text
    data = await state.get_data()
    device_id = data['device_id']
    user_id = message.from_user.id
    # await publish_message(mqtt_client, user_id, device_id, f"timer:{timer}")
    await publish.set_timer(mqtt_client, user_id, device_id, timer)
    await state.clear()
    await message.answer("Таймер успешно задан.", reply_markup=inline_builder(
        ["<< Назад"],
        [f"device_{device_id}"],
        [1]
    ))


@router.message(DeviceControl.timer)
async def set_timer(message: Message, state: FSMContext):
    data = await state.get_data()
    device_id = data['device_id']
    await message.answer("Время должно быть числом \nВведите число еще раз.", reply_markup=inline_builder(
        ["<< Назад"],
        [f"device_{device_id}"],
        [1]))


@router.callback_query(F.data == "delete")
async def cb_device_management_instruction(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.delete()
