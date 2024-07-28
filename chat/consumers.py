import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.template.loader import get_template
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Message
from .utils import get_group_name

User = get_user_model()


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            self.accept() # Accept before closing so automatic reconnection is not attempted by the HTMX WS extension
            self.close()
            return
        
        self.group_name = get_group_name(self.user)
        
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        if not hasattr(self, 'group_name'):
            return
        
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )

    def receive(self, text_data):
        # if not self.are_friends:
        #     return
        print(self.scope)

        json_data = json.loads(text_data)
        content = json_data['content'].strip()
        if not content or content.isspace():
            return
        
        other_user = get_object_or_404(User, username='user3')
        message = self.create_message(other_user, content)

        async_to_sync(self.channel_layer.group_send)(
            get_group_name(message.recipient), {
                'type': 'chat_message',
                'message': message
            }
        )

        html = self.create_html_message(message)
        self.send(text_data=html)

    def create_message(self, other_user, content):
        return Message.objects.create(
            sender=self.user,
            recipient=other_user,
            content=content
        )
    
    def create_html_message(self, message):
        return get_template('chat/snippets/htmx_message.html').render(
            context={
                'msg': message,
                'user': self.user
            }
        )

    def chat_message(self, event):
        message = event['message']
        if message.recipient == self.user:
            message.read = True
            message.save()

            async_to_sync(self.channel_layer.group_send)(
                get_group_name(message.sender), {
                    'type': 'message_read',
                    'message': message
                }
            )

        html = self.create_html_message(message)
        self.send(text_data=html)

    def message_read(self, event):
        message = event['message']
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