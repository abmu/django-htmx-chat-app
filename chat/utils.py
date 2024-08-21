from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()


def get_group_name(user):
    return f'chat_{user.id}'


def send_ws_message(user, event):
    group_name = get_group_name(user)
    async_to_sync(channel_layer.group_send)(
        group_name, event
    )


def send_ws_message_both_users(user_1, user_2, event):
    for user, other_user in [
        (user_1, user_2),
        (user_2, user_1)
    ]:
        event['other_user'] = other_user.serialize()
        send_ws_message(user, event=event)