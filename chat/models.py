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
    def get_grouped_messages(cls, request_user, other_user):
        '''Returns the messages sent directly between two users, grouped by date sent'''
        all_messages = cls.objects.filter(
            models.Q(sender=request_user, recipient=other_user) |
            models.Q(sender=other_user, recipient=request_user)
        ).order_by('timestamp')

        grouped_messages = {}
        new_message_found = False
        for message in all_messages:
            date = message.timestamp.date()
            if date not in grouped_messages:
                grouped_messages[date] = {
                    'date': date,
                    'messages': []
                }
            
            is_new = not message.read and message.recipient == request_user
            is_first_new = is_new and not new_message_found
            if is_first_new:
                new_message_found = True

            grouped_messages[date]['messages'].append({
                'sender': message.sender,
                'recipient': message.recipient,
                'content': message.content,
                'timestamp': message.timestamp,
                'was_read': message.read,
                'is_first_new': is_first_new
            })

            if is_new:
                message.read = True
                message.save()

        messages = sorted(grouped_messages.values(), key=lambda group: group['date'])
        return messages
    
    @classmethod
    def get_recent_chats(cls, user):
        '''Returns chat info for each of a user's chats, ordered by most recent activity'''
        user_messages = cls.objects.filter(
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

            if other_user.id not in chats:
                chats[other_user.id] = {
                    'other_user': other_user,
                    'last_sender': message.sender,
                    'last_content': message.content,
                    'last_timestamp': message.timestamp,
                    'unread_count': 0
                }
            elif chats[other_user.id]['last_timestamp'] < message.timestamp:
                chats[other_user.id].update({
                    'last_sender': message.sender,
                    'last_content': message.content,
                    'last_timestamp': message.timestamp,
                })

            if is_unread:
                chats[other_user.id]['unread_count'] += 1
        
        recent_chats = sorted(chats.values(), key=lambda msg: msg['last_timestamp'], reverse=True)
        return recent_chats

    @classmethod
    def remove_redundant_messages(cls):
        '''Remove messages where both the sender and recipient have deleted their accounts'''
        cls.objects.filter(sender__is_active=False, recipient__is_active=False).delete()