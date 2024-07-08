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

    def __str__(self):
        return self.content
    
    @classmethod
    def get_messages(cls, user1, user2):
        '''Returns all of the messages sent directly between two users'''
        return cls.objects.filter(
            models.Q(sender=user1, recipient=user2) |
            models.Q(sender=user2, recipient=user1)
        ).order_by('timestamp')
    
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
                    'last_message': message.content,
                    'timestamp': message.timestamp
                }

        # CAN CHOOSE TO SORT HERE OR IN TEMPLATE
        # recent_chats = sorted(chats.values(), key=lambda msg: msg['timestamp'], reverse=True)

        return chats.values()


