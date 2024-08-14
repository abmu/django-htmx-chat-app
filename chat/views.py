from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .models import Message

User = get_user_model()


def get_home_context(user):
    return {
        'recent_chats': Message.get_recent_chats(user),
        'incoming_requests': user.get_incoming_requests()
    }


@login_required(redirect_field_name=None)
def home(request):
    user = request.user

    return render(request, 'chat/home.html', {
            'title': 'Home',
        } | get_home_context(user)
    )


def direct_message(request, uuid):
    user = request.user
    current_other_user = get_object_or_404(User, uuid=uuid)
    are_friends = user.has_friend_mutual(current_other_user)
    messages = Message.get_messages(user, current_other_user)
    
    return render(request, 'chat/direct_message.html', {
            'title': f'Chat - {current_other_user.username}',
            'current_other_user': current_other_user,
            'are_friends': are_friends,
            'all_messages': messages
        } | get_home_context(user)
    )