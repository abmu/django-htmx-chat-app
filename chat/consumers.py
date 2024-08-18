import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.exceptions import ValidationError
from django.template.loader import get_template
from django.contrib.auth import get_user_model
from .models import Message
from .utils import get_group_name, send_ws_message_both_users

User = get_user_model()


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            self.accept() # Accept before closing so automatic reconnection is not attempted by the HTMX WS extension
            self.close()
            return
        
        self.user_group = get_group_name(self.user)
        
        async_to_sync(self.channel_layer.group_add)(
            self.user_group, self.channel_name
        )

        self.current_path = None
        self.current_other_user = None
        self.are_friends = None

        self.accept()

    def disconnect(self, close_code):
        if not hasattr(self, 'user_group'):
            return

        async_to_sync(self.channel_layer.group_discard)(
            self.user_group, self.channel_name
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
        elif message_type == 'page_load':
            path = json_data.get('path')
            self.handle_page_load(path)
        elif message_type == 'chat_load':
            uuid = json_data.get('uuid')
            self.handle_chat_load(uuid)

    def handle_page_load(self, path):
        self.current_path = path
        
    def handle_chat_load(self, uuid):
        try:
            self.current_other_user = User.objects.get(uuid=uuid)
        except User.DoesNotExist:
            return
        except ValidationError:
            return

        self.are_friends = self.user.has_friend_mutual(self.current_other_user)

    def handle_chat_send(self, content):
        if not self.are_friends:
            return
        
        if not isinstance(content, str):
            return
        
        content = content.strip()
        if not content:
            return
        
        message = self._create_message(content)
        serialized_message = message.serialize()

        event = {
            'type': 'chat_message',
            'serialized_message': serialized_message
        }
        send_ws_message_both_users(self.user, self.current_other_user, event)

    def _create_message(self, content):
        return Message.objects.create(
            sender=self.user,
            recipient=self.current_other_user,
            content=content
        )
    
    def _create_message_html(self, serialized_message):
        return get_template('chat/snippets/message.html').render(
            context={
                'message': serialized_message,
                'user': self.user
            }
        )
    
    def _create_recent_chat_html(self, serialized_message, other_user, unread_count):
        return get_template('chat/snippets/recent_chat.html').render(
            context={
                'last_message': serialized_message,
                'user': self.user,
                'other_user': other_user,
                'unread_count': unread_count
            }
        )
    
    def _is_recipient(self, data):
        return data['recipient']['uuid'] == str(self.user.uuid)
    
    def _is_current_other_user(self, serialized_other_user):
        return self.current_other_user and serialized_other_user['uuid'] == str(self.current_other_user.uuid)
    
    def _send_recent_chat_html(self, recent_chat_html):
        self.send(text_data=json.dumps({
            'type': 'recent_chat_html',
            'html': recent_chat_html
        }))

    def _send_message_html(self, message_html):
        self.send(text_data=json.dumps({
            'type': 'message_html',
            'html': message_html
        }))

    def chat_message(self, event):
        serialized_message = event['serialized_message']
        other_user = event['other_user']

        is_recipient = self._is_recipient(serialized_message)
        is_on_relevant_chat = self._is_current_other_user(other_user)

        unread_count = 0
        if is_recipient:
            if is_on_relevant_chat:
                self._mark_message_as_read(serialized_message)
                serialized_message['read'] = 'True'
            else:
                unread_count = 'INCREMENT' # increment unread count value on the client side

        recent_chat_html = self._create_recent_chat_html(serialized_message, other_user, unread_count)
        self._send_recent_chat_html(recent_chat_html)

        if not is_on_relevant_chat:
            return

        message_html = self._create_message_html(serialized_message)
        self._send_message_html(message_html)

    def _mark_message_as_read(self, serialized_message):
        # Update the 'read' status of the message in the database and notify the sender and recipient, only if the database hasn't already been updated
        newly_updated = Message.objects.filter(uuid=serialized_message['uuid'], read=False).update(read=True)

        if newly_updated > 0:
            event = {
                'type': 'message_read',
                'serialized_message': serialized_message
            }
            send_ws_message_both_users(self.user, self.current_other_user, event)

    def _send_decrement_unread_count(self, other_user, unread_count):
        self.send(text_data=json.dumps({
            'type': 'decrement_unread_count',
            'otherUserUuid': other_user['uuid'],
            'unreadCount': unread_count
        }))

    def _send_update_recent_chat_read_status(self, other_user):
        self.send(text_data=json.dumps({
            'type': 'update_recent_chat_read_status',
            'otherUserUuid': other_user['uuid']
        }))

    def _send_update_message_read_status(self, serialized_message):
        self.send(text_data=json.dumps({
            'type': 'update_message_read_status',
            'messageUuid': serialized_message['uuid']
        }))

    def _send_update_all_messages_read_status(self, chat):
        self.send(text_data=json.dumps({
            'type': 'update_all_messages_read_status',
            'senderUuid': chat['sender']['uuid']
        }))

    def _handle_read_event(self, event, is_all_messages):
        other_user = event['other_user']
        is_recipient = self._is_recipient(event['chat' if is_all_messages else 'serialized_message'])
        is_on_relevant_chat = self._is_current_other_user(other_user)

        if is_recipient:
            if not is_on_relevant_chat:
                # Update unread count if the user is the recipient and read the message but is not on the relevant chat (ie. they read message on another tab)
                # The unread count would have already been updated if the user was on the relevant chat
                unread_count = event['chat']['unread_count'] if is_all_messages else 1
                self._send_decrement_unread_count(other_user, unread_count)
        else:
            self._send_update_recent_chat_read_status(other_user)
            if is_on_relevant_chat:
                if is_all_messages:
                    self._send_update_all_messages_read_status(event['chat'])
                else:
                    self._send_update_message_read_status(event['serialized_message'])

    def message_read(self, event):
        self._handle_read_event(event, is_all_messages=False)

    def all_messages_read(self, event):
        self._handle_read_event(event, is_all_messages=True)

    def _update_consumer_friendship_status(self, other_user, new_status):
        if not self._is_current_other_user(other_user):
            return
        
        self.are_friends = new_status

    def friendship_created(self, event):
        self.send(text_data=json.dumps(event))

        other_user = event['other_user']
        self._update_consumer_friendship_status(other_user, True)

    def friendship_removed(self, event):
        self.send(text_data=json.dumps(event))

        other_user = event['other_user']
        self._update_consumer_friendship_status(other_user, False)

    def friend_request_sent(self, event):
        self.send(text_data=json.dumps(event))

    def friend_request_rejected(self, event):
        self.send(text_data=json.dumps(event))

    def friend_request_cancelled(self, event):
        self.send(text_data=json.dumps(event))




    # SEND WS MESSAGE AND SHOW DELETED ACCOUNT IN CHAT LIST INSTEAD - OR SHOULD I JUST LEAVE IT?

    def friend_account_deleted(self, event):
        self.send(text_data=json.dumps(event))

        other_user = event['other_user']
        self.update_consumer_friendship_status(other_user, False)

    def account_deleted(self, event):
        self.send(text_data=json.dumps(event))
        
        self.close()