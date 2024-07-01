from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import MessageForm
from .models import Message


@login_required(redirect_field_name=None)
def home(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            form.instance.sender = request.user
            form.save()
            return redirect('chat_home')
    else:
        form = MessageForm()

    sent_messages = Message.objects.filter(sender=request.user)

    return render(request, 'chat/home.html', {
        'title': 'Home',
        'form': form,
        'sent_messages': sent_messages
    })