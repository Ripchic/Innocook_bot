# from motor.core import AgnosticDatabase as MDB
# from paho.mqtt.client import Client
# import asyncio
#
#
# def on_status(client, userdata, msg):
#     print(f'Received status`{msg.payload.decode()}` from `{msg.topic}` topic')
#
#
# def on_notification(client, userdata, msg):
#     print(f'Received `{msg.payload.decode()}` from `{msg.topic}` topic')
#
#
# def on_error(client, userdata, msg):
#     print(f'Received `{msg.payload.decode()}` from `{msg.topic}` topic')
#
#
# async def database_registration(db: MDB, mqtt: Client):
#     # async def on_registration(client, userdata, msg):
#     print(f'Received `{msg.payload.decode()}` from `{msg.topic}` topic')
#     user_id = msg.payload.decode()
#     user = await db.users.find_one({"_id": user_id})
#     # increment a number of connections
#     connections = user["connections"] + 1
#     # Update the user in the database
#     # await db.users.update_one({"_id": user_id}, {"$set": {"connections": connections}})
#
#     # send id of a new device
#     mqtt.publish(f"{user_id}", f"{connections}")
#
#     def on_registration_sync(client, userdata, msg):
#         # Get the current event loop
#         loop = asyncio.get_event_loop()
#         # Schedule the coroutine to run within the current event loop
#         loop.create_task(on_registration(client, userdata, msg))
#
#
#     return on_registration_sync
#
#
# def create_on_registration_handler(db: MDB, mqtt: Client):
#     def on_registration(client, userdata, message):
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         loop.run_until_complete(handle_registration(db, client, message, mqtt))
#
#     return on_registration
#
#
# async def handle_registration(db, client, message, mqtt):
#     user_id = message.payload.decode()
#     print(f"Registration message received for user_id: {user_id}")
#
#     # Access MongoDB and get user connections
#     result = await db.users.find_one({"user_id": user_id})
#     if result:
#         connections = result.get("connections", [])
#         # Publish the connections back to the user_id topic
#         response_topic = f"user/{user_id}"
#         mqtt.publish(f"{user_id}", f"{connections}")
#         print(f"Connections for user_id {user_id} published to topic {response_topic}")
#     else:
#         print(f"No user found with user_id: {user_id}")
