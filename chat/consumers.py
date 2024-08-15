import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.exceptions import ValidationError
from django.template.loader import get_template
from django.contrib.auth import get_user_model
from .models import Message
from .utils import get_group_name, send_ws_message

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
        
        # if self.current_other_user is not None:
        #     self.handle_chat_unload()

        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )

    def receive(self, text_data):
        try:
            json_data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        
        message_type = json_data.get('type')
        if message_type == 'chat_send':
            content = json_data.get('content')
            self.handle_chat_send(content)
        elif message_type == 'chat_load':
            uuid = json_data.get('uuid')
            self.handle_chat_load(uuid)
        elif message_type == 'chat_unload':
            self.handle_chat_unload()
        
    def handle_chat_load(self, uuid):
        try:
            self.current_other_user = User.objects.get(uuid=uuid)
        except User.DoesNotExist:
            return
        except ValidationError:
            return

        self.current_other_user_group = get_group_name(self.current_other_user)
        self.are_friends = self.user.has_friend_mutual(self.current_other_user)

    def handle_chat_unload(self):
        self.current_other_user = None
        self.current_other_user_group = None
        self.are_friends = None

    def handle_chat_send(self, content):
        if not self.are_friends:
            return
        
        if not isinstance(content, str):
            return
        
        content = content.strip()
        if not content:
            return
        
        message = self.create_message(content)

        groups = [self.group_name, self.current_other_user_group]
        send_ws_message(
            groups, {
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
        return get_template('chat/snippets/message.html').render(
            context={
                'message': serialized_message,
                'user': self.user
            }
        )
    
    def create_recent_chat_html(self, other_user, message):
        serialized_message = message.serialize(limit_content=True)
        return get_template('chat/snippets/recent_chat.html').render(
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
        self.send(text_data=json.dumps({
            'type': 'recent_chat_html',
            'html': recent_chat_html
        }))

        is_current_chat_message = other_user == self.current_other_user
        if not is_current_chat_message:
            return

        is_recipient = message.recipient == self.user
        if is_recipient:
            self.mark_message_as_read(message)
            message.read = True

        message_html = self.create_message_html(message)
        self.send(text_data=json.dumps({
            'type': 'message_html',
            'html': message_html
        }))

    def mark_message_as_read(self, message):
        # Update the 'read' status of the message in the database and notify the sender and recipient, only if the database hasn't already been updated
        newly_updated = Message.objects.filter(uuid=message.uuid, read=False).update(read=True)

        if newly_updated > 0:
            groups = [self.group_name, self.current_other_user_group]
            send_ws_message(
                groups, {
                    'type': 'message_read',
                    'message': message
                }
            )

    def message_read(self, event):
        message = event['message']
        serialized_message = message.serialize()
        other_user = message.other_user(self.user)

        self.send(text_data=json.dumps({
            'type': 'message_read',
            'otherUserUuid': str(other_user.uuid),
            'message': {
                'uuid': serialized_message['uuid'],
                'recipientUuid': serialized_message['recipient']['uuid']
            }
        }))

    def all_messages_read(self, event):
        sender = event['sender']
        recipient = event['recipient']
        unread_count = event['unread_count']

        sender_uuid = str(sender.uuid)
        recipient_uuid = str(recipient.uuid)
        other_user_uuid = recipient_uuid if sender == self.user else sender_uuid

        self.send(text_data=json.dumps({
            'type': 'all_messages_read',
            'otherUserUuid': other_user_uuid,
            'chat': {
                'senderUuid': sender_uuid,
                'recipientUuid': recipient_uuid,
                'unreadCount': unread_count
            }
        }))





    # SEND AND CHECK IF THE USERNAME OF FRIEND WHO ADDED/REMOVED/DELETED IS CURRENT
    # WHAT HAPPENS IF USER DELETES ACCOUNT BUT THEY HAVE A CHAT OPEN IN ANOTHER TAB - SEND A MESSAGE TO CLOSE CONNECTION?
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