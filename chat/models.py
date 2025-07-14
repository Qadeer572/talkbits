from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f'{self.sender.username} to {self.receiver.username}: {self.content[:50]}'

class GroupChat(models.Model):
    name = models.CharField(max_length=100, unique=True)
    members = models.ManyToManyField(User, related_name='group_chats')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    created_at = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class GroupMessage(models.Model):
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f'{self.sender.username} in {self.group.name}: {self.content[:50]}'

class FileMessage(models.Model):
    MESSAGE_TYPES = [
        ('file', 'File'),
        ('audio', 'Audio'),
        ('image', 'Image'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,related_name='sent_files')
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE, null=True, blank=True,related_name='received_files')
    file = models.FileField(upload_to='chat_files/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f'{self.sender.username}: {self.file_name}'