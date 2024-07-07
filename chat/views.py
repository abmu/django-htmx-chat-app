from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from .forms import MessageForm, AddForm
from .models import Message

User = get_user_model()


@login_required(redirect_field_name=None)
def home(request):
    user = request.user
    friends_mutual = user.friends_mutual
    outgoing_requests = user.get_outgoing_requests()
    incoming_requests = user.get_incoming_requests()
    
    return render(request, 'chat/home.html', {
        'title': 'Home',
        'friends_mutual': friends_mutual,
        'outgoing_requests': outgoing_requests,
        'incoming_requests': incoming_requests
    })


@login_required(redirect_field_name=None)
@require_POST
def handle_incoming_request(request, user_id):
    user = request.user
    request_sender = get_object_or_404(User, id=user_id)

    if request_sender in user.get_incoming_requests():
        if 'accept' in request.POST:
            user.friends.add(request_sender)
        elif 'reject' in request.POST:
            request_sender.friends.remove(user)
        else:
            messages.error(request, 'Invalid action')
    else:
        messages.error(request, 'No such friend request')

    return redirect('chat_home')


@login_required(redirect_field_name=None)
@require_POST
def handle_outgoing_request(request, user_id):
    user = request.user
    request_recipient = get_object_or_404(User, id=user_id)

    if request_recipient in user.get_outgoing_requests():
        user.friends.remove(request_recipient)
    else:
        messages.error(request, 'No such friend request')

    return redirect('chat_home')


@login_required(redirect_field_name=None)
@require_POST
def remove_friend(request, user_id):
    user = request.user
    friend = get_object_or_404(User, id=user_id)

    if friend in user.friends_mutual:
        user.friends.remove(friend)
        friend.friends.remove(user)
    else:
        messages.error(request, 'No such user in your friends list')

    return redirect('chat_home')


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

    messages = Message.get_messages(sender, recipient)
    
    return render(request, 'chat/direct_message.html', {
        'title': 'Direct message',
        'form': form,
        'recipient': recipient,
        'all_messages': messages
    })


@login_required
def add_user(request):
    if request.method == 'POST':
        form = AddForm(request.POST, initial={'user': request.user})
        if form.is_valid():
            form.save(request.user)
            return redirect('chat_add_user')
    else:
        form = AddForm()

    return render(request, 'chat/add_user.html', {
        'title': 'Home',
        'form': form
    })