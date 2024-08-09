from mqtt.setup import publish_message
from motor.core import AgnosticDatabase as MDB
from paho.mqtt.client import Client
import json
from typing import Any, Dict


def create_payload(command: str, **kwargs: Any) -> str:
    payload = {"command": command}
    payload.update(kwargs)
    return json.dumps(payload)


def convert_timer(timer: str) -> int:
    """Convert a timer string (e.g., '1.30' or '2') to minutes."""
    if '.' in timer:
        minutes, seconds = map(int, timer.split('.'))
        return minutes * 60 + seconds
    else:
        return int(timer) * 60


async def get_status(client: Client, user_id: int, device_id: int, message_id=int) -> Any:
    """
    Request the status of the device.
    """
    payload = create_payload("status", message_id=message_id)
    return await publish_message(client, user_id, device_id, payload)


async def set_power(client: Client, user_id: int, device_id: int, power: str) -> Any:
    """
    Set the power state of the device.
    """
    payload = create_payload("power", state=power)
    return await publish_message(client, user_id, device_id, payload)


async def set_preset(client: Client, user_id: int, device_id: int, preset: dict) -> Any:
    """
    Apply a preset setting to the device.
    """
    temp = preset["temp"]
    timer = convert_timer(preset["timer"])

    payload = create_payload("preset", temp=temp, timer=timer)
    return await publish_message(client, user_id, device_id, payload)


async def new_device(client: Client, user_id: int, db: MDB):
    """
    New device registration.
    """
    user = await db.users.find_one({"_id": user_id})
    print(user)
    connections = int(user["connections"])
    payload = create_payload(command=str(user_id), new_id=connections)
    # device_id = -1 means registration
    print(user_id, payload)
    return await publish_message(client, user_id, -1, payload)
