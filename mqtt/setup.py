import logging
import time
from dotenv import load_dotenv
import os
import asyncio
import json

from paho.mqtt import client as mqtt_client

from mqtt import subscribe as sub

from motor.core import AgnosticDatabase as MDB

load_dotenv()
BROKER = os.getenv('MQTT_BROKER')
PORT = int(os.getenv('MQTT_PORT'))
CLIENT_ID = 'TELEGRAM_BOT'
USERNAME = os.getenv('MQTT_USERNAME')
PASSWORD = os.getenv('MQTT_PASSWORD')

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

FLAG_EXIT = False


def on_connect(client, userdata, flags, rc):
    if rc == 0 and client.is_connected():
        print("Connected to MQTT Broker!")
    else:
        print(f'Failed to connect, return code {rc}')


def on_disconnect(client, userdata, rc):
    logging.info("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logging.info("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            logging.info("Reconnected successfully!")
            return
        except Exception as err:
            logging.error("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)
    global FLAG_EXIT
    FLAG_EXIT = True


def on_message(client, userdata, msg):
    print(f'Received `{msg.payload.decode()}` from `{msg.topic}` topic')


async def publish_message(cli, user_id, device_name, payload):
    topic = f'{user_id}/{device_name}'
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, cli.publish, topic, payload)
    status = result[0]
    if status == 0:
        print(f"Sent `{payload}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")


def init_client():
    client = mqtt_client.Client(client_id=CLIENT_ID, clean_session=False)
    client.username_pw_set(USERNAME, PASSWORD)
    client.connect_async(BROKER, PORT, keepalive=120)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.subscribe("status")
    client.subscribe("notification")
    client.subscribe("error")
    client.subscribe("new_device")
    client.subscribe("reg_conf")

    client.loop_start()

    # get the main event loop
    loop = asyncio.get_event_loop()

    def topic(sub):
        def decorator(coro):
            async def async_wrapper(client, userdata, msg):
                await coro(client, userdata, msg)

            @client.topic_callback(sub)
            def handle(client, userdata, msg):
                asyncio.run_coroutine_threadsafe(async_wrapper(client, userdata, msg), loop)

        return decorator

    return client, topic


def connect_mqtt(db: MDB):
    client, topic = init_client()

    @topic("status")
    async def on_status(client, userdata, msg):
        print("Status message received")
        await asyncio.sleep(1)
        # Process status message

    @topic("notification")
    async def on_notification(client, userdata, msg):
        print("Notification message received")
        await asyncio.sleep(1)
        # Process notification message

    @topic("error")
    async def on_error(client, userdata, msg):
        print("Error message received")
        await asyncio.sleep(1)
        # Process error message

    @topic("new_device")
    async def database_registration(client, userdata, msg):
        print("Registration message received")
        user_id = int(msg.payload.decode())
        # print(f"{user_id}")
        user = await db.users.find_one({"_id": user_id})
        # print(f"{user}")
        connections = user["connections"]
        # print(f"Connections for user_id {user_id} incremented to {connections}")
        # await db.users.update_one({"_id": user_id}, {"$set": {"connections": connections}})
        print(f"{user_id}; {connections}")
        client.publish(f"{user_id}", f"{connections}")
        print(f"Connections for user_id {user_id} published to topic {user_id}")
        # print(f"Connections for user_id {user_id} published to topic {user_id}")
        # Process registration message

    @topic("reg_conf")
    async def registration_confirmation(client, userdata, msg):
        print("Registration confirmation message received")
        message = msg.payload.decode()
        print(message)
        parsed_message = json.loads(message)
        user_id = int(parsed_message["user_id"])
        device_id = int(parsed_message["device_id"])
        print(f"User {user_id} has successfully registered a new device {device_id}")
        user = await db.users.find_one({"_id": user_id})
        db.users.update_one({"_id": user_id},
                                  {"$push": {"devices": {"device_id": device_id, "name": "Новое устройство"}}})
        connections = user["connections"] + 1
        db.users.update_one({"_id": user_id}, {"$set": {"connections": connections}})
    return client
