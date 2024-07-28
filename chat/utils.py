from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()


def get_group_name(user):
    return f'chat{user.id}'


def send_ws_message(group_name, event):
    async_to_sync(channel_layer.group_send)(
        group_name, event
    )