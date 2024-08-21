import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.exceptions import ValidationError
from django.template.loader import get_template
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Message
from .utils import get_group_name, send_ws_message_both_users

User = get_user_model()


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.scope['csrf_token'] = self.scope['cookies'].get('csrftoken')
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

    def _create_message(self, content):
        return Message.objects.create(
            sender=self.user,
            recipient=self.current_other_user,
            content=content
        )

    @staticmethod
    def _get_chat_message_event(serialized_message):
        return {
            'type': 'chat_message',
            'serialized_message': serialized_message
        }

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

        event = self._get_chat_message_event(serialized_message)
        send_ws_message_both_users(self.user, self.current_other_user, event=event)
    
    def _is_recipient(self, data):
        return data['recipient']['uuid'] == str(self.user.uuid)
    
    def _is_current_other_user(self, serialized_other_user):
        return self.current_other_user and serialized_other_user['uuid'] == str(self.current_other_user.uuid)
    
    def _create_recent_chat_html(self, serialized_message, other_user, unread_count):
        return get_template('chat/snippets/recent_chat.html').render(
            context={
                'last_message': serialized_message,
                'user': self.user,
                'other_user': other_user,
                'unread_count': unread_count
            }
        )
    
    def _send_recent_chat_html(self, recent_chat_html):
        self.send(text_data=json.dumps({
            'type': 'recent_chat_html',
            'html': recent_chat_html
        }))

    def _create_message_html(self, serialized_message):
        return get_template('chat/snippets/message.html').render(
            context={
                'message': serialized_message,
                'user': self.user
            }
        )

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
                unread_count = 'increment' # Increment unread count value on the client side

        recent_chat_html = self._create_recent_chat_html(serialized_message, other_user, unread_count)
        self._send_recent_chat_html(recent_chat_html)

        if not is_on_relevant_chat:
            return
        
        message_html = self._create_message_html(serialized_message)
        self._send_message_html(message_html)

    @staticmethod
    def _get_message_read_event(serialized_message):
        return {
            'type': 'message_read',
            'serialized_message': serialized_message
        }

    def _mark_message_as_read(self, serialized_message):
        # Update the 'read' status of the message in the database and notify the sender and recipient, only if the database hasn't already been updated
        newly_updated = Message.objects.filter(uuid=serialized_message['uuid'], read=False).update(read=True)

        if newly_updated > 0:
            event = self._get_message_read_event(serialized_message)
            send_ws_message_both_users(self.user, self.current_other_user, event=event)

    def _send_decrement_unread_count(self, other_user, count):
        self.send(text_data=json.dumps({
            'type': 'decrement_unread_count',
            'otherUserUuid': other_user['uuid'],
            'count': count
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

    def _handle_read_event(self, event, is_all_messages_read):
        other_user = event['other_user']
        is_recipient = self._is_recipient(event['chat' if is_all_messages_read else 'serialized_message'])
        is_on_relevant_chat = self._is_current_other_user(other_user)

        if is_recipient:
            if not is_on_relevant_chat:
                # Update unread count if the user is the recipient and read the message but is not on the relevant chat (ie. they read message on another tab)
                # The unread count would have already been updated if the user was on the relevant chat
                count = event['chat']['unread_count'] if is_all_messages_read else 1
                self._send_decrement_unread_count(other_user, count)
        else:
            self._send_update_recent_chat_read_status(other_user)

            if not is_on_relevant_chat:
                return
            
            if is_all_messages_read:
                self._send_update_all_messages_read_status(event['chat'])
            else:
                self._send_update_message_read_status(event['serialized_message'])

    def message_read(self, event):
        self._handle_read_event(event, is_all_messages_read=False)

    def all_messages_read(self, event):
        self._handle_read_event(event, is_all_messages_read=True)

    def _send_update_section_count(self, page, section, action):
        '''
        Sends a message to update the count for a specific section on a specific page
        - page: "home" or "manage_friends"
        - section: "incoming", "outgoing", or "friends"
        - action "increment" or "decrement"
        '''
        self.send(text_data=json.dumps({
            'type': 'update_section_count',
            'page': page,
            'section': section,
            'action': action
        }))

    def _send_remove_user_from_section(self, section, other_user):
        '''
        Sends a message to remove a user from a specific section on the manage friends page
        - section: "incoming", "outgoing", or "friends"
        '''
        self.send(text_data=json.dumps({
            'type': 'remove_user_from_section',
            'section': section,
            'otherUserUuid': other_user['uuid']
        }))

    def _create_incoming_request_html(self, sender):
        return get_template('users/snippets/incoming_request.html').render(
            context={
                'sender': sender,
                'csrf_token': self.scope['csrf_token']
            }
        )

    def _create_outgoing_request_html(self, recipient):
        return get_template('users/snippets/outgoing_request.html').render(
            context={
                'recipient': recipient,
                'csrf_token': self.scope['csrf_token']
            }
        )

    def _send_add_user_html_to_section(self, section, user_html):
        '''
        Sends a message to add a new user to a specific section on the manage friends page
        - section: "incoming", "outgoing", or "friends"
        '''
        self.send(text_data=json.dumps({
            'type': 'add_user_html_to_section',
            'section': section,
            'html': user_html
        }))

    def _handle_friend_request_event(self, event, is_friend_request_removed):
        other_user = event['other_user']
        is_recipient = self._is_recipient(event['request'])
        section = 'incoming' if is_recipient else 'outgoing'
        count_action = 'decrement' if is_friend_request_removed else 'increment'

        if is_recipient:
            self._send_update_section_count('home', section, count_action)

        if not self.current_path.startswith(reverse('manage_friends')):
            return
        
        self._send_update_section_count('manage_friends', section, count_action)

        if self.current_path == reverse('incoming_requests') and is_recipient:
            if is_friend_request_removed:
                self._send_remove_user_from_section(section, other_user)
            else:
                incoming_request_html = self._create_incoming_request_html(other_user)
                self._send_add_user_html_to_section(section, incoming_request_html)
        elif self.current_path == reverse('outgoing_requests') and not is_recipient:
            if is_friend_request_removed:
                self._send_remove_user_from_section(section, other_user)
            else:
                outgoing_request_html = self._create_outgoing_request_html(other_user)
                self._send_add_user_html_to_section(section, outgoing_request_html)
    
    def _create_friend_html(self, friend):
        return get_template('users/snippets/friend.html').render(
            context={
                'friend': friend,
                'csrf_token': self.scope['csrf_token']
            }
        )
    
    def _send_update_friendship(self, are_friends):
        self.send(text_data=json.dumps({
            'type': 'update_friendship',
            'areFriends': are_friends
        }))

    def _handle_friendship_change(self, event, are_friends):
        other_user = event['other_user']
        section = 'friends'
        count_action = 'increment' if are_friends else 'decrement'

        if self.current_path.startswith(reverse('manage_friends')):
            self._send_update_section_count('manage_friends', section, count_action)

            if self.current_path != reverse('friends_list'):
                return
            
            if are_friends:
                friend_html = self._create_friend_html(other_user)
                self._send_add_user_html_to_section(section, friend_html)
            else:
                self._send_remove_user_from_section(section, other_user)
        elif self._is_current_other_user(other_user):
            self.are_friends = are_friends
            self._send_update_friendship(are_friends)

    def friend_request_accepted(self, event):
        self._handle_friend_request_event(event, is_friend_request_removed=True)
        self._handle_friendship_change(event, are_friends=True)

    def friend_removed(self, event):
       self._handle_friendship_change(event, are_friends=False)

    def friend_request_sent(self, event):
        self._handle_friend_request_event(event, is_friend_request_removed=False)

    def friend_request_rejected(self, event):
        self._handle_friend_request_event(event, is_friend_request_removed=True)

    def friend_request_cancelled(self, event):
        self._handle_friend_request_event(event, is_friend_request_removed=True)

    def _send_account_deleted(self):
        self.send(text_data=json.dumps({
            'type': 'account_deleted'
        }))

    def account_deleted(self, event):
        self._send_account_deleted()
        
        self.close()