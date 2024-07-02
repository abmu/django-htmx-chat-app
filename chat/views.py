from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import MessageForm
from .models import Message


@login_required(redirect_field_name=None)
def home(request):
    received_messages = Message.objects.filter(recipient=request.user)

    return render(request, 'chat/home.html', {
        'title': 'Home',
        'received_messages': received_messages
    })


def direct_message(request, username):
    sender = request.user
    recipient = get_object_or_404(get_user_model(), username=username)

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
    
    return render(request, 'chat/direct_message.html', {
        'title': 'Direct message',
        'form': form,
        'recipient': recipient,
        'sent_messages': sent_messages
    })