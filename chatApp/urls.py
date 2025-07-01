 
from django.contrib import admin
from django.urls import path,include
from . import views
urlpatterns = [
    path('',views.chat_view, name='chat'),  # Main chat view
     
]
