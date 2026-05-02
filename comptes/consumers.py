import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            # Rejoindre un groupe spécifique à l'utilisateur
            self.group_name = f'user_{self.user.id}'
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # On peut ignorer les messages venant du client
        pass

    async def send_notification(self, event):
        # Envoyer la notification au client WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message'],
            'url': event.get('url', '#'),
        }))