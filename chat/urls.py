from django.urls import path , include
from . import views 
urlpatterns = [
     path('chat/<str:room_name>/', views.chat_room, name='chat'),
     path('group/<str:group_name>/', views.group_chat, name='group_chat'),
]