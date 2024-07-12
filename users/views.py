from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import AddForm
from .models import User


@login_required
def manage_friends(request):
    return redirect('friends_list')


@login_required
def friends_list(request):
    user = request.user
    friends_mutual = user.friends_mutual

    return render(request, 'users/friends_list.html', {
        'title': 'All friends',
        'friends_mutual': friends_mutual
    })


@login_required(redirect_field_name=None)
@require_POST
def remove_friend(request, user_id):
    user = request.user
    friend = get_object_or_404(User, id=user_id)

    if user.friends_mutual.contains(friend):
        user.friends.remove(friend)
        friend.friends.remove(user)
    else:
        messages.error(request, 'No such user in your friends list')

    return redirect('friends_list')


@login_required
def incoming_requests(request):
    user = request.user
    incoming_requests = user.get_incoming_requests()

    return render(request, 'users/incoming_requests.html', {
        'title': 'Incoming requests',
        'incoming_requests': incoming_requests
    })


@login_required(redirect_field_name=None)
@require_POST
def handle_incoming_request(request, user_id):
    user = request.user
    request_sender = get_object_or_404(User, id=user_id)

    if user.get_incoming_requests().contains(request_sender):
        if 'accept' in request.POST:
            user.friends.add(request_sender)
        elif 'reject' in request.POST:
            request_sender.friends.remove(user)
        else:
            messages.error(request, 'Invalid action')
    else:
        messages.error(request, 'No such friend request')

    return redirect('incoming_requests')


@login_required
def outgoing_requests(request):
    user = request.user
    outgoing_requests = user.get_outgoing_requests()

    return render(request, 'users/outgoing_requests.html', {
        'title': 'Outgoing requests',
        'outgoing_requests': outgoing_requests
    })


@login_required(redirect_field_name=None)
@require_POST
def cancel_outgoing_request(request, user_id):
    user = request.user
    request_recipient = get_object_or_404(User, id=user_id)

    if user.get_outgoing_requests().contains(request_recipient):
        user.friends.remove(request_recipient)
    else:
        messages.error(request, 'No such friend request')

    return redirect('outgoing_requests')


@login_required
def add_friend(request):
    if request.method == 'POST':
        form = AddForm(request.POST, initial={'user': request.user})
        if form.is_valid():
            form.save(request.user)
            return redirect('add_friend')
    else:
        form = AddForm()

    return render(request, 'users/add_friend.html', {
        'title': 'Add friend',
        'form': form
    })


@login_required
def settings(request):
    return redirect('account_email')