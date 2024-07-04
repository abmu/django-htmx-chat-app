from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import MessageForm, AddForm
from .models import Message

User = get_user_model()


@login_required(redirect_field_name=None)
def home(request):
    user = request.user
    friends = user.friends.filter(friends=user)
    outgoing_requests = user.friends.exclude(pk__in=friends)
    incoming_requests = User.objects.filter(friends=user).exclude(pk__in=friends)

    return render(request, 'chat/home.html', {
        'title': 'Home',
        'outgoing_requests': outgoing_requests,
        'incoming_requests': incoming_requests,
        'friends': friends
    })


@login_required
def direct_message(request, username):
    sender = request.user
    recipient = get_object_or_404(User, username=username)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            form.instance.sender = sender
            form.instance.recipient = recipient
            form.save()
            return redirect('chat_direct_message', username)
    else:
        form = MessageForm()

    sent_messages = Message.objects.filter(sender=sender, recipient=recipient)
    print(sent_messages.last().content)
    
    return render(request, 'chat/direct_message.html', {
        'title': 'Direct message',
        'form': form,
        'recipient': recipient,
        'sent_messages': sent_messages
    })


@login_required
def add_user(request):
    if request.method == 'POST':
        form = AddForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            return redirect('chat_add_user')
    else:
        form = AddForm()

    return render(request, 'chat/add_user.html', {
        'title': 'Home',
        'form': form
    })