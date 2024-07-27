import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.template.loader import get_template
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Message
from .utils import get_chat_group_name, get_notification_group_name

User = get_user_model()


class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            self.accept() # Accept before closing so automatic reconnection is not attempted by the HTMX WS extension
            self.close()
            return
        
        self.group_name = get_notification_group_name(self.user)
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        ) 

        self.accept()

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            self.accept()
            self.close()
            return
        
        other_user_username = self.scope['url_route']['kwargs']['username']
        self.other_user = get_object_or_404(User, username=other_user_username)
        if not self.other_user.is_active:
            self.accept()
            self.close()
            return
        self.are_friends = self.user.has_friend_mutual(self.other_user)

        self.group_name = get_chat_group_name(self.user, self.other_user)
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name, self.channel_name
            )

    def receive(self, text_data):
        if not self.user.is_authenticated:
            self.send(text_data=json.dumps({
                'type': 'not_authenticated'
            }))
            self.close()
            return
        elif not self.are_friends:
            return

        json_data = json.loads(text_data)
        content = json_data['content']
        if not content or content.isspace():
            return
        message = self.create_message(content.strip())

        event = {
            'type': 'chat_message',
            'message': message,
        }

        async_to_sync(self.channel_layer.group_send)(
            self.group_name, event
        )

    def create_message(self, content):
        return Message.objects.create(
            sender=self.user,
            recipient=self.other_user,
            content=content
        )

    def chat_message(self, event):
        message = event['message']
        if self.user == message.recipient:
            message.read = True
            message.save()

            async_to_sync(self.channel_layer.group_send)(
                self.group_name, {
                    'type': 'message_read',
                    'message': message
                }
            )

        html = get_template('chat/snippets/htmx_message.html').render(
            context={
                'msg': message,
                'user': self.user
            }
        )

        self.send(text_data=html)

    def message_read(self, event):
        message = event['message']
        if self.user != message.sender:
            return

        self.send(text_data=json.dumps({
            'type': 'message_read',
            'messageId': f'{message.uuid}'
        }))

    def all_messages_read(self, event):
        self.send(text_data=json.dumps({
            'type': 'all_messages_read'
        }))

    def friendship_created(self, event):
        self.are_friends = True
        self.send(text_data=json.dumps({
            'type': 'friendship_created'
        }))

    def friendship_removed(self, event):
        self.are_friends = False
        self.send(text_data=json.dumps({
            'type': 'friendship_removed'
        }))

    def friend_account_deleted(self, event):
        self.send(text_data=json.dumps({
            'type': 'friend_account_deleted'
        }))
        self.close()