from aiogram.fsm.state import State, StatesGroup


class DeviceManagement(StatesGroup):
    add_name = State()
    remove_name = State()


class DeviceControl(StatesGroup):
    temperature = State()
    timer = State()


class PresetsManagement(StatesGroup):
    name = State()
    temp = State()
    timer = State()
    edit_name = State()
    edit_temp = State()
    edit_timer = State()