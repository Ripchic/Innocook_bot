from mqtt.setup import publish_message
from motor.core import AgnosticDatabase
from paho.mqtt.client import Client


async def get_status(client: Client, user_id, device_id):
    return await publish_message(client, user_id, device_id, "status")


async def set_power(client: Client, user_id, device_id, power: str):
    return await publish_message(client, user_id, device_id, f"power:{power}")


async def set_preset(client: Client, user_id, device_id, preset_id, db: AgnosticDatabase):
    user = await db.users.find_one({"_id": user_id})
    user_presets = user["presets"]
    preset = user_presets[preset_id]
    temp = preset["temp"]
    timer = preset["timer"]
    if '.' in timer:
        timer = timer.split('.')
        timer = int(timer[0]) * 60 + int(timer[1])
    else:
        timer = int(timer) * 60
    print(timer)
    return await publish_message(client, user_id, device_id, f"preset:{{temp:{temp}; timer:{timer}}}")
