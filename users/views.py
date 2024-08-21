from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from chat.views import get_home_context
from .forms import AddFriendForm, DeleteAccountForm
from .models import User


def get_friends_context(user):
    return get_home_context(user) | {
        'friends_mutual': user.friends_mutual,
        'outgoing_requests': user.get_outgoing_requests()
    } 


def get_csrf_token(request):
    return request.COOKIES.get('csrftoken')


def manage_friends(request):
    return redirect('friends_list')


@never_cache
def friends_list(request):
    user = request.user

    if request.method == 'POST':
        uuid = request.POST.get('uuid')
        friend = get_object_or_404(User, uuid=uuid)
        
        success, message = user.remove_friend(friend)
        if not success:
            messages.error(request, message)

        return redirect('friends_list')

    return render(request, 'users/friends_list.html', {
            'title': 'Friends list',
            'csrf_token': get_csrf_token(request)
        } | get_friends_context(user)
    )


@never_cache
def incoming_requests(request):
    user = request.user

    if request.method == 'POST':
        uuid = request.POST.get('uuid')
        request_sender = get_object_or_404(User, uuid=uuid)

        action = request.POST.get('action')
        success, message = user.handle_incoming_request(request_sender, action)
        if not success:
            messages.error(request, message)
        
        return redirect('incoming_requests')

    return render(request, 'users/incoming_requests.html', {
            'title': 'Incoming requests',
            'csrf_token': get_csrf_token(request)
        } | get_friends_context(user)
    )


@never_cache
def outgoing_requests(request):
    user = request.user

    if request.method == 'POST':
        uuid = request.POST.get('uuid')
        request_recipient = get_object_or_404(User, uuid=uuid)

        success, message = user.cancel_outgoing_request(request_recipient)
        if not success:
            messages.error(request, message)

        return redirect('outgoing_requests')

    return render(request, 'users/outgoing_requests.html', {
            'title': 'Outgoing requests',
            'csrf_token': get_csrf_token(request)
        } | get_friends_context(user)
    )
    

@never_cache
def add_friend(request):
    user = request.user

    if request.method == 'POST':
        form = AddFriendForm(request.POST, initial={'user': user})
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            messages.success(request, f'You have successfully sent a friend request to {username}')
            return redirect('add_friend')
    else:
        form = AddFriendForm()

    return render(request, 'users/add_friend.html', {
            'title': 'Add friend',
            'form': form,
        } | get_friends_context(user)
    )


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