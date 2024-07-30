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

        self.current_other_user = None
        self.other_user_group_name = None
        self.are_friends = None

        self.accept()

    def disconnect(self, close_code):
        if not hasattr(self, 'group_name'):
            return
        
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
        
        if self.current_other_user is not None:
            self.handle_chat_unload()

    def receive(self, text_data):
        json_data = json.loads(text_data)
        message_type = json_data['type']
        if message_type == 'chat_load':
            other_user = json_data['other_user']
            self.handle_chat_load(other_user)
        elif message_type == 'chat_unload':
            self.handle_chat_unload()
        elif message_type == 'chat_send':
            content = json_data['content']
            self.handle_chat_send(content)

    def handle_chat_load(self, username):
        self.current_other_user = get_object_or_404(User, username=username)
        self.other_user_group_name = get_group_name(self.current_other_user)
        self.are_friends = self.user.has_friend_mutual(self.current_other_user)

    def handle_chat_unload(self):
        self.current_other_user = None
        self.other_user_group_name = None
        self.are_friends = None

    def handle_chat_send(self, content):
        if not self.are_friends:
            return
        
        content = content.strip()
        if not content or content.isspace():
            return
        
        message = self.create_message(content)

        for group_name in [self.group_name, self.other_user_group_name]:
            async_to_sync(self.channel_layer.group_send)(
                group_name, {
                    'type': 'chat_message',
                    'message': message
                }
            )

    def create_message(self, content):
        return Message.objects.create(
            sender=self.user,
            recipient=self.current_other_user,
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

        # ONLY SHOW FIRST X CHARACTERS OF MESSAGE IF NOT ON THAT CHAT

        if message.recipient == self.user:
            if message.sender == self.current_other_user:
                message.read = True
                message.save()

                async_to_sync(self.channel_layer.group_send)(
                    self.other_user_group_name, {
                        'type': 'message_read',
                        'message': message
                    }
                )

                html = self.create_html_message(message)
                self.send(text_data=html)
            else:
                self.send(text_data=json.dumps({
                    'type': 'new_message'
                }))
        elif message.sender == self.user:
            if message.recipient == self.current_other_user:
                html = self.create_html_message(message)
                self.send(text_data=html)
            else:
                self.send(text_data=json.dumps({
                    'type': 'new_message'
                }))

    def message_read(self, event):
        print('read')
        message = event['message']
        self.send(text_data=json.dumps({
            'type': 'message_read',
            'messageId': f'{message.uuid}'
        }))

    def all_messages_read(self, event):
        self.send(text_data=json.dumps({
            'type': 'all_messages_read'
        }))

    # SEND THE USERNAME OF FRIEND WHO ADDED/REMOVED/DELETED

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