from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import MessageForm
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
    recipient = get_object_or_404(User, username__iexact=username)
    is_friends = sender.friends_mutual.contains(recipient)

    if request.method == 'POST':
        if not is_friends:
            return redirect('direct_message', username)
        form = MessageForm(request.POST)
        if form.is_valid():
            form.instance.sender = sender
            form.instance.recipient = recipient
            form.save()
            return redirect('direct_message', username)
    else:
        form = MessageForm()

    grouped_messages = Message.get_grouped_messages(sender, recipient)
    
    return render(request, 'chat/direct_message.html', {
        'title': 'Direct message',
        'form': form,
        'recipient': recipient,
        'grouped_messages': grouped_messages,
        'is_friends': is_friends
    })