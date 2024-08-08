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
        self.current_other_user_group = None
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
        if message_type == 'chat_send':
            content = json_data['content']
            self.handle_chat_send(content)
        elif message_type == 'chat_load':
            current_other_user = json_data['current_other_user']
            self.handle_chat_load(current_other_user)
        elif message_type == 'chat_unload':
            self.handle_chat_unload()
        
    def handle_chat_load(self, username):
        self.current_other_user = get_object_or_404(User, username=username)
        self.current_other_user_group = get_group_name(self.current_other_user)
        self.are_friends = self.user.has_friend_mutual(self.current_other_user)

    def handle_chat_unload(self):
        self.current_other_user = None
        self.current_other_user_group = None
        self.are_friends = None

    def handle_chat_send(self, content):
        if not self.are_friends:
            return
        
        content = content.strip()
        if not content or content.isspace():
            return
        
        message = self.create_message(content)

        for group_name in [self.group_name, self.current_other_user_group]:
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
    
    def create_message_html(self, message):
        serialized_message = message.serialize()
        return get_template('chat/snippets/htmx_message.html').render(
            context={
                'message': serialized_message,
                'user': self.user
            }
        )
    
    def create_recent_chat_html(self, other_user, message):
        serialized_message = message.serialize(limit_content=True)
        return get_template('chat/snippets/htmx_recent_chat.html').render(
            context={
                'other_user': other_user,
                'last_message': serialized_message,
                'user': self.user
            }
        )

    def chat_message(self, event):
        message = event['message']
        other_user = message.other_user(self.user)

        recent_chat_html = self.create_recent_chat_html(other_user, message)
        self.send(text_data=recent_chat_html)

        is_current_chat_message = other_user == self.current_other_user
        if not is_current_chat_message:
            return

        is_recipient = message.recipient == self.user
        if is_recipient:
            self.mark_message_as_read(message)
            message.read = True

        message_html = self.create_message_html(message)
        self.send(text_data=message_html)

    def mark_message_as_read(self, message):
        # Update the 'read' status of the message in the database and notify the sender and recipient, only if the database hasn't already been updated
        newly_updated = Message.objects.filter(uuid=message.uuid, read=False).update(read=True)

        if newly_updated > 0:
            for group_name in [self.group_name, self.current_other_user_group]:
                async_to_sync(self.channel_layer.group_send)(
                    group_name, {
                        'type': 'message_read',
                        'message': message
                    }
                )

    def message_read(self, event):
        message = event['message']
        other_user = message.other_user(self.user)

        self.send(text_data=json.dumps({
            'type': 'message_read',
            'message': message.serialize(),
            'otherUser': other_user.username
        }))

    def all_messages_read(self, event):
        sender = event['sender']
        recipient = event['recipient']
        unread_count = event['unread_count']
        other_user = recipient if sender == self.user else sender

        self.send(text_data=json.dumps({
            'type': 'all_messages_read',
            'chat': {
                'sender': sender.username,
                'recipient': recipient.username,
                'unread': unread_count
            },
            'otherUser': other_user.username
        }))





    # SEND AND CHECK IF THE USERNAME OF FRIEND WHO ADDED/REMOVED/DELETED IS CURRENT
    # SHOW DELETED ACCOUNT IN CHAT LIST





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