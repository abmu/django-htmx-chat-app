from django.db import models
from django.conf import settings
from django.utils import timezone


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name='received_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)

    def __str__(self):
        return self.content
    
    @classmethod
    def get_messages(cls, request_user, other_user):
        '''Returns the old and new unread messages sent directly between two users'''
        all_messages = cls.objects.filter(
            models.Q(sender=request_user, recipient=other_user) |
            models.Q(sender=other_user, recipient=request_user)
        ).order_by('-timestamp')

        new_messages = all_messages.filter(recipient=request_user, read=False)
        new_messages_pk = []
        new_messages_list = []
        for message in new_messages: # evaluate lazy queryset before the messages are updated
            new_messages_pk.append(message.pk)
            new_messages_list.append(message)
        new_messages.update(read=True)

        old_messages = all_messages.exclude(pk__in=new_messages_pk)

        return {
            'old': old_messages,
            'new': new_messages_list
        }
    
    @classmethod
    def get_recent_chats(cls, user):
        '''Returns chat info for each of a user's chats, ordered by most recent activity'''
        user_messages = cls.objects.filter(
            models.Q(sender=user) |
            models.Q(recipient=user)
        ).select_related('sender', 'recipient')

        chats = {}
        for message in user_messages:
            other_user = message.recipient if message.sender == user else message.sender
            if other_user.id not in chats or chats[other_user.id]['timestamp'] < message.timestamp:
                chats[other_user.id] = {
                    'other_user': other_user,
                    'last_sender': message.sender,
                    'last_content': message.content,
                    'timestamp': message.timestamp
                }
        
        recent_chats = sorted(chats.values(), key=lambda msg: msg['timestamp'], reverse=True)
        return recent_chats


