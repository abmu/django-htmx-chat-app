from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import MessageForm
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
            return redirect('direct_message', username)
    else:
        form = MessageForm()

    messages = Message.get_messages(sender, recipient)
    
    return render(request, 'chat/direct_message.html', {
        'title': 'Direct message',
        'form': form,
        'recipient': recipient,
        'all_messages': messages
    })