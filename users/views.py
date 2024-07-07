from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import AddForm
from .models import User


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
def add_user(request):
    if request.method == 'POST':
        form = AddForm(request.POST, initial={'user': request.user})
        if form.is_valid():
            form.save(request.user)
            return redirect('add_user')
    else:
        form = AddForm()

    return render(request, 'users/add_user.html', {
        'title': 'Home',
        'form': form
    })