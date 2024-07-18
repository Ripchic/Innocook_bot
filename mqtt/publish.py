from mqtt.setup import publish_message
from motor.core import AgnosticDatabase
from paho.mqtt.client import Client


async def get_status(client: Client, user_id, device_id):
    return await publish_message(client, user_id, device_id, "status")


async def set_power(client: Client, user_id, device_id, power: str):
    return await publish_message(client, user_id, device_id, f"power:{power}")


async def set_temperature(client: Client, user_id, device_id, temperature: str):
    return await publish_message(client, user_id, device_id, f"temp:{temperature}")


async def set_timer(client: Client, user_id, device_id, timer: str):
    return await publish_message(client, user_id, device_id, f"timer:{timer}")


async def set_preset(client: Client, user_id, device_id, preset_id, db: AgnosticDatabase):
    user = await db.users.find_one({"_id": user_id})
    user_presets = user["presets"]
    preset = user_presets[preset_id]
    return await publish_message(client, user_id, device_id, f"preset:{preset}")
