from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
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
    return redirect('friends_list')


@never_cache
def direct_message(request, uuid):
    user = request.user
    current_other_user = get_object_or_404(User, uuid=uuid)
    are_friends = user.has_friend_mutual(current_other_user)

    if request.method == 'POST':
        form = MessageForm(request.POST, initial={'sender': user, 'recipient': current_other_user, 'are_friends': are_friends})
        if form.is_valid():
            form.save()
            return redirect('direct_message', current_other_user.uuid)
    else:
        form = MessageForm()

    chat_messages = Message.get_messages(user, current_other_user)
    
    return render(request, 'chat/direct_message.html', {
            'title': f'Chat - {current_other_user.username}',
            'current_other_user': current_other_user,
            'are_friends': are_friends,
            'form': form,
            'chat_messages': chat_messages
        } | get_home_context(user)
    )