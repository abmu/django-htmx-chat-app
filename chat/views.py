from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .models import Message

User = get_user_model()


@login_required(redirect_field_name=None)
def home(request):
    recent_chats = Message.get_recent_chats(request.user)

    return render(request, 'chat/home.html', {
        'title': 'Home',
        'recent_chats': recent_chats
    })


@login_required
def direct_message(request, username):
    sender = request.user
    current_other_user = get_object_or_404(User, username__iexact=username)
    are_friends = sender.has_friend_mutual(current_other_user)
    grouped_messages = Message.get_grouped_messages(sender, current_other_user)
    recent_chats = Message.get_recent_chats(request.user)
    
    return render(request, 'chat/direct_message.html', {
        'title': 'Direct message',
        'recent_chats': recent_chats,
        'current_other_user': current_other_user,
        'are_friends': are_friends,
        'grouped_messages': grouped_messages
    })