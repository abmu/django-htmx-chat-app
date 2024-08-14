from django.db import models
from django.conf import settings
from django.utils import timezone
from uuid import uuid4
from .utils import get_group_name, send_ws_message


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
    
    def get_date(self):
        return self.timestamp.strftime("%Y-%m-%d")
    
    def serialize(self, limit_content=False):
        visible_characters = 10
        content = self.content[:visible_characters] + '...' if limit_content and len(self.content) > visible_characters else self.content
        return {
            'uuid': str(self.uuid),
            'sender': {
                'uuid': str(self.sender.uuid),
                'username': self.sender.username
            },
            'recipient': {
                'uuid': str(self.recipient.uuid),
                'username': self.recipient.username
            },
            'content': content,
            'timestamp': self.timestamp.isoformat(),
            'read': str(self.read)
        }
    
    def other_user(self, user):
        return self.recipient if self.sender == user else self.sender
    
    @classmethod
    def get_messages(cls, request_user, other_user):
        '''Returns the messages sent directly between two users'''
        messages = cls.objects.filter(
            models.Q(sender=request_user, recipient=other_user) |
            models.Q(sender=other_user, recipient=request_user)
        ).order_by('-timestamp')

        messages_list = []
        for message in messages:
            messages_list.append(message.serialize())

        new_messages = messages.filter(read=False, sender=other_user)
        if new_messages.exists():
            unread_count = new_messages.count()
            new_messages.update(read=True)

            groups = [get_group_name(request_user), get_group_name(other_user)]
            send_ws_message(
                groups, {
                    'type': 'all_messages_read',
                    'sender': other_user,
                    'recipient': request_user,
                    'unread_count': unread_count
                }
            )

        return messages_list
    
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

            serialized_message = message.serialize(limit_content=True)

            if other_user.id not in chats:
                chats[other_user.id] = {
                    'other_user': other_user,
                    'last_message': serialized_message,
                    'last_timestamp': message.timestamp,
                    'unread_count': 0
                }
            elif chats[other_user.id]['last_timestamp'] < message.timestamp:
                chats[other_user.id].update({
                    'last_message': serialized_message,
                    'last_timestamp': message.timestamp
                })

            if is_unread:
                chats[other_user.id]['unread_count'] += 1
        
        recent_chats = sorted(chats.values(), key=lambda msg: msg['last_timestamp'], reverse=True)
        return recent_chats

    @classmethod
    def remove_redundant_messages(cls):
        '''Remove all messages from the database where both the sender and recipient have deleted their accounts'''
        cls.objects.filter(sender__is_active=False, recipient__is_active=False).delete()