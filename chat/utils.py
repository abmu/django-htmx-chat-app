from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()


def get_group_name(user):
    return f'chat_{user.id}'


def send_ws_message(groups, event):
    for group_name in groups:
        async_to_sync(channel_layer.group_send)(
            group_name, event
        )