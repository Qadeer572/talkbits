import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

# Track first user per room
initiators = set()

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.username = self.scope['user'].username
        user1 = self.username
        user2 = self.room_name
        self.room_group_name = f"chat_{''.join(sorted([user1, user2]))}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        initiators.discard(self.username)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            print(f"Received message: {data}")

            handlers = {
                "call_request": self.handle_call_request,
                "call_accept": self.handle_call_accept,
                "call_reject": self.handle_call_reject,
                "call_cancelled": self.handle_call_cancelled,
                "join": self.handle_join,
                "offer": self.handle_offer,
                "answer": self.handle_answer,
                "candidate": self.handle_candidate,
                "call_ended": self.handle_call_ended,
            }

            handler = handlers.get(data["type"])
            if handler:
                await handler(data)
            else:
                print(f"No handler for message type {data['type']}")
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {data['type']}"
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))

    async def handle_call_request(self, data):
        if data.get("from") != self.username:
            print(f"Ignoring call_request from {data.get('from')} (not this user)")
            return

        call_type = data.get("call_type", "audio")
        if call_type not in ["audio", "video"]:
            call_type = "audio"

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "call_request_message",
                "sender": self.channel_name,
                "message": {
                    "type": "call_request",
                    "from": self.username,
                    "to": data.get("to"),
                    "call_type": call_type
                }
            }
        )

    async def handle_call_accept(self, data):
        if data.get("from") != self.username:
            print(f"Ignoring call_accept from {data.get('from')} (not this user)")
            return

        call_type = data.get("call_type", "audio")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "call_response",
                "sender": self.channel_name,
                "message": {
                    "type": "call_accept",
                    "from": self.username,
                    "to": data.get("to"),
                    "call_type": call_type
                }
            }
        )

    async def handle_call_reject(self, data):
        if data.get("from") != self.username:
            print(f"Ignoring call_reject from {data.get('from')} (not this user)")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "call_reject_message",
                "sender": self.channel_name,
                "message": {
                    "type": "call_reject",
                    "from": self.username,
                    "to": data.get("to"),
                    "reason": data.get("reason", "Call rejected")
                }
            }
        )
        # Clean up initiator status
        initiators.discard(self.username)
        initiators.discard(data.get("to"))

    async def handle_call_cancelled(self, data):
        if data.get("from") != self.username:
            print(f"Ignoring call_cancelled from {data.get('from')} (not this user)")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "call_cancelled_message",
                "sender": self.channel_name,
                "message": {
                    "type": "call_cancelled",
                    "from": self.username,
                    "to": data.get("to")
                }
            }
        )
        # Clean up initiator status
        initiators.discard(self.username)
        initiators.discard(data.get("to"))

    async def handle_join(self, data):
        if data.get("username") != self.username:
            print(f"Ignoring join from {data.get('username')} (not this user)")
            return

        initiator = self.username not in initiators
        if initiator:
            initiators.add(self.username)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "join_ack",
                "sender": self.channel_name,
                "message": {
                    "type": "join_ack",
                    "username": self.username,
                    "call_room": data.get("call_room"),
                    "initiator": initiator,
                    "call_type": data.get("call_type", "audio")
                }
            }
        )

    async def handle_offer(self, data):
        if data.get("username") == self.username:
            print(f"Ignoring offer from self ({self.username})")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_sdp",
                "sender": self.channel_name,
                "message": {
                    "type": "offer",
                    "username": data.get("username"),
                    "sdp": data.get("sdp"),
                    "call_type": data.get("call_type", "audio")
                }
            }
        )

    async def handle_answer(self, data):
        if data.get("username") == self.username:
            print(f"Ignoring answer from self ({self.username})")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_sdp",
                "sender": self.channel_name,
                "message": {
                    "type": "answer",
                    "username": data.get("username"),
                    "sdp": data.get("sdp"),
                    "call_type": data.get("call_type", "audio")
                }
            }
        )

    async def handle_candidate(self, data):
        if data.get("username") == self.username:
            print(f"Ignoring candidate from self ({self.username})")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_sdp",
                "sender": self.channel_name,
                "message": {
                    "type": "candidate",
                    "username": data.get("username"),
                    "candidate": data.get("candidate"),
                    "call_type": data.get("call_type", "audio")
                }
            }
        )

    async def handle_call_ended(self, data):
        if data.get("from") == self.username:
            print(f"Ignoring call_ended from self ({self.username})")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "call_ended_message",
                "sender": self.channel_name,
                "message": {
                    "type": "call_ended",
                    "from": data.get("from"),
                    "to": data.get("to"),
                    "reason": data.get("reason", "Call ended")
                }
            }
        )
        # Clean up initiator status for all users in the room
        initiators.discard(self.username)
        initiators.discard(data.get("to"))

    async def call_request_message(self, event):
        message = event["message"]
        if message.get("to") != self.username or self.channel_name == event.get("sender"):
            print(f"Ignoring call_request for {message.get('to')} (not this user: {self.username})")
            return
        await self.send(text_data=json.dumps(event["message"]))

    async def call_response(self, event):
        if self.channel_name != event.get("sender"):
            await self.send(text_data=json.dumps(event["message"]))

    async def call_reject_message(self, event):
        message = event["message"]
        if message.get("to") != self.username or self.channel_name == event.get("sender"):
            print(f"Ignoring call_reject for {message.get('to')} (not this user: {self.username})")
            return
        await self.send(text_data=json.dumps(event["message"]))
        # Close connection after rejection
        initiators.discard(self.username)
        initiators.discard(message.get("from"))
        await self.close(code=1000)

    async def call_cancelled_message(self, event):
        message = event["message"]
        if message.get("to") != self.username or self.channel_name == event.get("sender"):
            print(f"Ignoring call_cancelled for {message.get('to')} (not this user: {self.username})")
            return
        await self.send(text_data=json.dumps(event["message"]))
        initiators.discard(self.username)
        initiators.discard(message.get("from"))

    async def send_sdp(self, event):
        if self.channel_name != event.get("sender"):
            await self.send(text_data=json.dumps(event["message"]))

    async def join_ack(self, event):
        if self.channel_name != event.get("sender"):
            await self.send(text_data=json.dumps(event["message"]))

    async def call_ended_message(self, event):
        message = event["message"]
        if message.get("to") != self.username and message.get("from") != self.username:
            print(f"Ignoring call_ended for {message.get('to')} (not this user: {self.username})")
            return
        if self.channel_name != event.get("sender"):
            await self.send(text_data=json.dumps(event["message"]))
            # Close connection for all participants
            initiators.discard(self.username)
            initiators.discard(message.get("from"))
            initiators.discard(message.get("to"))
            await self.close(code=1000)