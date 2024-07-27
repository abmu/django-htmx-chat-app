from django.db import models
from django.conf import settings
from django.utils import timezone
from uuid import uuid4
from .utils import get_chat_group_name, send_ws_message


class Message(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)


    class Meta:
        indexes = [
            models.Index(fields=['sender', 'recipient'], name='sender_recipient_idx'),
            models.Index(fields=['sender'], name='sender_idx'),
            models.Index(fields=['recipient'], name='recipient_idx')
        ]

    def __str__(self):
        return self.content
    
    @classmethod
    def get_grouped_messages(cls, request_user, other_user):
        '''Returns the messages sent directly between two users, grouped by date sent'''
        messages = cls.objects.filter(
            models.Q(sender=request_user, recipient=other_user) |
            models.Q(sender=other_user, recipient=request_user)
        ).order_by('-timestamp')

        grouped_messages = {}
        for message in messages:
            date = message.timestamp.date()
            if date not in grouped_messages:
                grouped_messages[date] = {
                    'date': date,
                    'messages': []
                }
            
            grouped_messages[date]['messages'].append({
                'uuid': message.uuid,
                'sender': message.sender,
                'recipient': message.recipient,
                'content': message.content,
                'timestamp': message.timestamp,
                'read': message.read
            })

        new_messages = messages.filter(read=False, sender=other_user)
        if new_messages.exists():
            new_messages.update(read=True)

            group_name = get_chat_group_name(request_user, other_user)
            send_ws_message(group_name, {'type': 'all_messages_read'})

        sorted_grouped_messages = sorted(grouped_messages.values(), key=lambda group: group['date'], reverse=True)
        return sorted_grouped_messages
    
    @staticmethod
    def get_recent_chats(user):
        '''Returns chat info for each of a user's chats, ordered by most recent activity'''
        user_messages = Message.objects.filter(
            models.Q(sender=user) |
            models.Q(recipient=user)
        ).select_related('sender', 'recipient')

        chats = {}
        for message in user_messages:
            if message.sender == user:
                other_user = message.recipient
                is_unread = False
            else:
                other_user = message.sender
                is_unread = not message.read

            if other_user.username not in chats:
                chats[other_user.username] = {
                    'other_user': other_user,
                    'last_sender': message.sender,
                    'last_content': message.content,
                    'last_timestamp': message.timestamp,
                    'unread_count': 0
                }
            elif chats[other_user.username]['last_timestamp'] < message.timestamp:
                chats[other_user.username].update({
                    'last_sender': message.sender,
                    'last_content': message.content,
                    'last_timestamp': message.timestamp,
                })

            if is_unread:
                chats[other_user.username]['unread_count'] += 1
        
        recent_chats = sorted(chats.values(), key=lambda msg: msg['last_timestamp'], reverse=True)
        return recent_chats

    @staticmethod
    def remove_redundant_messages():
        '''Remove all messages from the database where both the sender and recipient have deleted their accounts'''
        Message.objects.filter(sender__is_active=False, recipient__is_active=False).delete()