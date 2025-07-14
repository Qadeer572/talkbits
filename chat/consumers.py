# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message,GroupMessage,GroupChat
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async



class ChatConsumer(AsyncWebsocketConsumer):
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
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = self.scope['user']  
        receiver = await self.get_receiver_user() 

        await self.save_message(sender, receiver, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            
            {
                'type': 'chat_message',
                'sender': sender.username,
                'receiver': receiver.username,
                'message': message
            }
        )
        

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        receiver = event['receiver']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'sender': sender,
            'receiver': receiver,
            'message': message
        }))

    @sync_to_async
    def save_message(self, sender, receiver, message):
        Message.objects.create(sender=sender, receiver=receiver, content=message)

    @sync_to_async
    def get_receiver_user(self):
        return User.objects.get(username=self.room_name)


class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'group_{self.room_name}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'file':
            await self.handle_file_message(data)
        elif message_type == 'audio':
            await self.handle_audio_message(data)
        else:
            await self.handle_text_message(data)

    async def handle_text_message(self, data):
        message = data['message']
        username = data['username']
        room_name = data['room_name']
        
        # Save message to database
        await self.save_group_message(username, room_name, message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'group_message',
                'message': message,
                'sender': username,
            }
        )

    async def handle_file_message(self, data):
        username = data['username']
        room_name = data['room_name']
        file_data = data['file']
        
        # Process file
        file_url = await self.save_group_file(file_data, username, room_name)
        
        # Send file message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'group_file_message',
                'file': {
                    'url': file_url,
                    'name': file_data['name']
                },
                'sender': username,
            }
        )

    async def handle_audio_message(self, data):
        username = data['username']
        room_name = data['room_name']
        audio_data = data['audio']
        
        # Process audio
        audio_url = await self.save_group_audio(audio_data, username, room_name)
        
        # Send audio message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'group_audio_message',
                'audio': {
                    'url': audio_url,
                    'name': audio_data['name']
                },
                'sender': username,
            }
        )

    async def group_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
        }))

    async def group_file_message(self, event):
        await self.send(text_data=json.dumps({
            'file': event['file'],
            'sender': event['sender'],
        }))

    async def group_audio_message(self, event):
        await self.send(text_data=json.dumps({
            'audio': event['audio'],
            'sender': event['sender'],
        }))

    @database_sync_to_async
    def save_group_message(self, username, room_name, message):
        sender = User.objects.get(username=username)
        group = GroupChat.objects.get(name=room_name)
        GroupMessage.objects.create(sender=sender, group=group, content=message)

    @database_sync_to_async
    def save_group_file(self, file_data, username, room_name):
        # Decode base64 file data
        format, filestr = file_data['data'].split(';base64,')
        ext = format.split('/')[-1]
        
        # Create file
        file_content = ContentFile(base64.b64decode(filestr), name=f"{uuid.uuid4()}.{ext}")
        file_path = default_storage.save(f'group_files/{file_content.name}', file_content)
        
        # Save to database
        sender = User.objects.get(username=username)
        group = GroupChat.objects.get(name=room_name)
        
        FileMessage.objects.create(
            sender=sender,
            group=group,
            file=file_path,
            file_name=file_data['name'],
            file_type='file'
        )
        
        return default_storage.url(file_path)

    @database_sync_to_async
    def save_group_audio(self, audio_data, username, room_name):
        # Decode base64 audio data
        format, audiostr = audio_data['data'].split(';base64,')
        ext = 'webm'
        
        # Create audio file
        audio_content = ContentFile(base64.b64decode(audiostr), name=f"{uuid.uuid4()}.{ext}")
        audio_path = default_storage.save(f'group_audio/{audio_content.name}', audio_content)
        
        # Save to database
        sender = User.objects.get(username=username)
        group = GroupChat.objects.get(name=room_name)
        
        FileMessage.objects.create(
            sender=sender,
            group=group,
            file=audio_path,
            file_name=audio_data['name'],
            file_type='audio'
        )
        
        return default_storage.url(audio_path)


 