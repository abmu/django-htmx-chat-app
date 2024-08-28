from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
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
 

@login_required(redirect_field_name=None)
def manage_friends(request):
    request.session['from_manage_friends'] = True
    return redirect('friends_list')


@login_required(redirect_field_name=None)
def friends_list(request):
    user = request.user

    if request.method == 'POST':
        uuid = request.POST.get('uuid')
        friend = get_object_or_404(User, uuid=uuid)
        
        success, message = user.remove_friend(friend)
        if not success:
            messages.error(request, message)

        return redirect('friends_list')

    context = {
        'title': 'Friends list',
        'csrf_token': get_csrf_token(request)
    }

    is_htmx_request = request.headers.get('HX-Request') == 'true'
    is_history_restore_request = request.headers.get('HX-History-Restore-Request') == 'true'
    is_full_load_request = request.headers.get('HX-Full-Page-Request') == 'true'
    from_home = request.session.pop('from_home', False)
    from_manage_friends = request.session.pop('from_manage_friends', False)

    if not is_htmx_request or is_history_restore_request or is_full_load_request or from_home:
        return render(request, 'users/friends_list.html', context | get_friends_context(user))
    
    if from_manage_friends:
        return render(request, 'users/friends_list.html',
            context | {
                'friends_mutual': user.friends_mutual,
                'incoming_requests': user.get_incoming_requests(),
                'outgoing_requests': user.get_outgoing_requests()
            }
        )
    
    return render(request, 'users/partials/friends_list.html',
        context | {
            'friends_mutual': user.friends_mutual
        }
    )


@login_required(redirect_field_name=None)
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

    context = {
        'title': 'Incoming requests',
        'csrf_token': get_csrf_token(request)
    }
    if request.headers.get('HX-Request') and not (request.headers.get('HX-History-Restore-Request') or request.headers.get('HX-Full-Page-Request')):
        return render(request, 'users/partials/incoming_requests.html',
            context | {
                'incoming_requests': user.get_incoming_requests()
            }
        )
    return render(request, 'users/incoming_requests.html', context | get_friends_context(user))


@login_required(redirect_field_name=None)
def outgoing_requests(request):
    user = request.user

    if request.method == 'POST':
        uuid = request.POST.get('uuid')
        request_recipient = get_object_or_404(User, uuid=uuid)

        success, message = user.cancel_outgoing_request(request_recipient)
        if not success:
            messages.error(request, message)

        return redirect('outgoing_requests')

    context = {
        'title': 'Outgoing requests',
        'csrf_token': get_csrf_token(request)
    }
    if request.headers.get('HX-Request') and not (request.headers.get('HX-History-Restore-Request') or request.headers.get('HX-Full-Page-Request')):
        return render(request, 'users/partials/outgoing_requests.html',
            context | {
                'outgoing_requests': user.get_outgoing_requests()
            }
        )
    return render(request, 'users/outgoing_requests.html', context | get_friends_context(user))
    

@login_required(redirect_field_name=None)
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

    context = {
        'title': 'Add friend',
        'form': form,
    }
    if request.headers.get('HX-Request') and not (request.headers.get('HX-History-Restore-Request') or request.headers.get('HX-Full-Page-Request')):
        return render(request, 'users/partials/add_friend.html', context)
    return render(request, 'users/add_friend.html', context | get_friends_context(user))


def settings(request):
    return redirect('account_email')


@login_required(redirect_field_name=None)
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