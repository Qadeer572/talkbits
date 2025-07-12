import json
from channels.generic.websocket import AsyncWebsocketConsumer

# Track first user per room
initiators = set()

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        user1 = self.scope['user'].username 
        user2 = self.room_name
        self.room_group_name = f"chat_{''.join(sorted([user1, user2]))}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)


    async def receive(self, text_data):
        data = json.loads(text_data)
      #  print("Debugging Message====>")
        print(f"Received message: {data}")  # Debug logging

        if data["type"] == "call_request":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "call_request",
                    "sender": self.channel_name,
                    "message": data
                }
            )
            return

        if data["type"] in ["call_accept", "call_reject"]:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "call_response",
                    "sender": self.channel_name,
                    "message": data
                }
            )
            return

        # Regular offer/answer/candidate flow
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_sdp",
                "sender": self.channel_name,
                "message": data
            }
        )

    async def send_sdp(self, event):
        if self.channel_name != event.get("sender"):
            await self.send(text_data=json.dumps(event["message"]))
            print(f"Sent SDP message to {self.username}: {event['message']}")  # Debug logging

    async def send_signal(self, event):
        if self.channel_name != event.get("sender"):
            await self.send(text_data=json.dumps(event["message"]))
            print(f"Sent signal to {self.username}: {event['message']}")  # Debug logging

    async def call_request(self, event):
        if self.channel_name != event.get("sender"):
            await self.send(text_data=json.dumps(event["message"]))
            print(f"Sent call_request to {self.username}: {event['message']}")  # Debug logging

    async def call_response(self, event):
        if self.channel_name != event.get("sender"):
            await self.send(text_data=json.dumps(event["message"]))
            print(f"Sent call_response to {self.username}: {event['message']}")  # Debug logging