from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()


def get_group_name(user_1, user_2):
    id_1 = user_1.id
    id_2 = user_2.id
    if id_1 < id_2:
        return f'chat_{id_1}_{id_2}'
    return f'chat_{id_2}_{id_1}'


def send_ws_message(group_name, message_type):
    async_to_sync(channel_layer.group_send)(
        group_name, {
            'type': message_type
        }
    )