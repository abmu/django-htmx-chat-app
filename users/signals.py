from allauth.account.signals import user_logged_out
from django.dispatch import receiver
from chat.utils import send_session_ws_message


def _get_account_logged_out_event():
    return {
        'type': 'account_logged_out'
    }


@receiver(user_logged_out)
def user_logged_in_handler(sender, request, user, **kwargs):
    session = request.session
    account_logged_out_event = _get_account_logged_out_event()
    send_session_ws_message(session, event=account_logged_out_event)