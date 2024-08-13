from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import AddFriendForm, DeleteAccountForm
from .models import User


def manage_friends(request):
    return redirect('friends_list')


def friends_list(request):
    user = request.user
    friends_mutual = user.friends_mutual

    return render(request, 'users/friends_list.html', {
        'title': 'All friends',
        'friends_mutual': friends_mutual
    })


@login_required(redirect_field_name=None)
@require_POST
def remove_friend(request, username):
    user = request.user
    friend = get_object_or_404(User, username=username)
    
    success, message = user.remove_friend(friend)
    if not success:
        messages.error(request, message)

    return redirect('friends_list')


def incoming_requests(request):
    user = request.user
    incoming_requests = user.get_incoming_requests()

    return render(request, 'users/incoming_requests.html', {
        'title': 'Incoming requests',
        'incoming_requests': incoming_requests
    })


@login_required(redirect_field_name=None)
@require_POST
def handle_incoming_request(request, username):
    user = request.user
    request_sender = get_object_or_404(User, username=username)

    action = request.POST.get('action')
    if action not in ('accept', 'reject'):
        action = None
    
    success, message = user.handle_incoming_request(request_sender, action)
    if not success:
        messages.error(request, message)

    return redirect('incoming_requests')


def outgoing_requests(request):
    user = request.user
    outgoing_requests = user.get_outgoing_requests()

    return render(request, 'users/outgoing_requests.html', {
        'title': 'Outgoing requests',
        'outgoing_requests': outgoing_requests
    })


@login_required(redirect_field_name=None)
@require_POST
def cancel_outgoing_request(request, username):
    user = request.user
    request_recipient = get_object_or_404(User, username=username)

    success, message = user.cancel_outgoing_request(request_recipient)
    if not success:
        messages.error(request, message)

    return redirect('outgoing_requests')


def add_friend(request):
    if request.method == 'POST':
        form = AddFriendForm(request.POST, initial={'user': request.user})
        if form.is_valid():
            form.save()
            return redirect('add_friend')
    else:
        form = AddFriendForm()

    return render(request, 'users/add_friend.html', {
        'title': 'Add friend',
        'form': form
    })


def settings(request):
    return redirect('account_email')


def delete_account(request):
    if request.method == 'POST':
        form = DeleteAccountForm(request.POST, initial={'user': request.user})
        if form.is_valid():
            user = request.user
            logout(request)
            user.delete_account()
            messages.success(request, 'Your account has successfully been deleted')
            return redirect('chat_home')
    else:
        form = DeleteAccountForm()

    return render(request, 'users/delete_account.html', {
        'title': 'Delete account',
        'form': form
    })