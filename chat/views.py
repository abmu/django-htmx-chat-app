from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .forms import MessageForm
from .models import Message

User = get_user_model()


def get_home_context(user):
    return {
        'recent_chats': Message.get_recent_chats(user),
        'incoming_requests': user.get_incoming_requests()
    }


@login_required(redirect_field_name=None)
def home(request):
    request.session['from_home'] = True
    return redirect('manage_friends')


@login_required(redirect_field_name=None)
def direct_message(request, uuid):
    user = request.user
    current_other_user = get_object_or_404(User, uuid=uuid)
    are_friends = user.has_friend_mutual(current_other_user)
    
    # A POST request is only made when a websocket message could not be sent
    if request.method == 'POST':
        form = MessageForm(request.POST, initial={'sender': user, 'recipient': current_other_user, 'are_friends': are_friends})
        if form.is_valid():
            form.save()
            return redirect('direct_message', current_other_user.uuid)
    else:
        form = MessageForm()

    chat_messages = Message.get_messages(user, current_other_user)

    context = {
        'title': f'Chat - {current_other_user.username}',
        'current_other_user': current_other_user,
        'are_friends': are_friends,
        'form': form,
        'chat_messages': chat_messages
    }
    if request.headers.get('HX-Request') and not request.headers.get('HX-History-Restore-Request'):
        return render(request, 'chat/partials/direct_message.html', context)
    return render(request, 'chat/direct_message.html', context | get_home_context(user))