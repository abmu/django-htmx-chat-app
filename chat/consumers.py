import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.template.loader import get_template


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.sender_id = self.scope['user'].id
        self.recipient_id = int(self.scope['url_route']['kwargs']['user_id'])
        self.group_name = f'chat_{min(self.sender_id, self.recipient_id)}_{max(self.sender_id, self.recipient_id)}'

        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        event = {
            'type': 'chat_message',
            'message': message
        }
        
        async_to_sync(self.channel_layer.group_send)(
            self.group_name, event
        )

    def chat_message(self, event):
        message = event['message']

        self.send(text_data=json.dumps({'message': message}))