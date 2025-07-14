from django.contrib import admin
from .models import Message,GroupMessage,GroupChat

admin.site.register(Message)
admin.site.register(GroupMessage)
admin.site.register(GroupChat)
