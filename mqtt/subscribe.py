def on_status(client, userdata, msg):
    print(f'Received `{msg.payload.decode()}` from `{msg.topic}` topic')


def on_notification(client, userdata, msg):
    print(f'Received `{msg.payload.decode()}` from `{msg.topic}` topic')


def on_error(client, userdata, msg):
    print(f'Received `{msg.payload.decode()}` from `{msg.topic}` topic')
