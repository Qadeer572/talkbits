# signaling/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"call_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("type") == "join":
            members = self.channel_layer.groups.get(self.room_group_name, [])
            is_initiator = len(members) == 1
            await self.send(text_data=json.dumps({
                "type": "join_ack",
                "initiator": is_initiator
            }))
            return  # 👈 don't send to group!

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_signal",
                "message": data
            }
        )


    async def send_signal(self, event):
        await self.send(text_data=json.dumps(event["message"]))
