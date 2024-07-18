import logging
import time
from dotenv import load_dotenv
import os
import asyncio

from paho.mqtt import client as mqtt_client

from mqtt import subscribe as sub

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


def connect_mqtt():
    client = mqtt_client.Client(client_id=CLIENT_ID, clean_session=False)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.connect(BROKER, PORT, keepalive=120)
    client.on_disconnect = on_disconnect

    # topic listeners
    client.message_callback_add("status", sub.on_status)
    client.message_callback_add("notification", sub.on_notification)
    client.message_callback_add("error", sub.on_error)
    client.on_message = on_message

    client.subscribe("status")
    client.subscribe("notification")
    client.subscribe("error")

    client.loop_start()
    return client
