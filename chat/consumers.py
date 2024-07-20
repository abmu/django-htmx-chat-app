import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.template.loader import get_template
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            self.close()
            return
        
        other_user_id = self.scope['url_route']['kwargs']['user_id']
        self.other_user = get_object_or_404(User, id=other_user_id)
        if not self.user.has_friend_mutual(self.other_user):
            self.close()
            return

        self.group_name = self.get_group_name(self.user.id, other_user_id)

        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )

        self.accept()

    @classmethod
    def get_group_name(cls, id_1, id_2):
        id_1 = int(id_1)
        id_2 = int(id_2)
        if id_1 < id_2:
            return f'chat_{id_1}_{id_2}'
        return f'chat_{id_2}_{id_1}'

    def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name, self.channel_name
            )

    def receive(self, text_data):
        if not self.user.is_authenticated or not self.user.has_friend_mutual(self.other_user):
            self.close()
            return

        json_data = json.loads(text_data)
        content = json_data['content']
        if not content or content.isspace():
            return
        message = self.create_message(content)

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

        html = get_template('chat/snippets/htmx_message.html').render(
            context={
                'msg': message,
                'user': self.user
            }
        )

        self.send(text_data=html)

    @classmethod
    def send_message_read_event(cls, channel_layer, group_name, message):
        async_to_sync(channel_layer.group_send)(
            group_name, {
                'type': 'message_read',
                'message': message 
            }
        )

    def message_read(self, event):
        message = event['message']
        self.send(text_data=f'{message.id}')