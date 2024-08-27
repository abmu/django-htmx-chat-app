from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()


def _group_send(group_name, event):
    async_to_sync(channel_layer.group_send)(
        group_name, event
    )


def get_session_group(session):
    return f'session_{session.session_key}'


def send_session_ws_message(session, event):
    group_name = get_session_group(session)
    _group_send(group_name, event)


def get_user_group(user):
    return f'user_{user.id}'


def send_user_ws_message(user, event):
    group_name = get_user_group(user)
    _group_send(group_name, event)


def send_both_users_ws_message(user_1, user_2, event):
    for user, other_user in [
        (user_1, user_2),
        (user_2, user_1)
    ]:
        event['other_user'] = other_user.serialize()
        send_user_ws_message(user, event=event)