from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Message,GroupChat,GroupMessage
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Max

@login_required
def chat_room(request, room_name):
    search_query = request.GET.get('search', '') 
    users = User.objects.exclude(id=request.user.id) 
    chats = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver__username=room_name)) |
        (Q(receiver=request.user) & Q(sender__username=room_name))
    )

    if search_query:
        chats = chats.filter(Q(content__icontains=search_query))  

    chats = chats.order_by('timestamp') 
    user_last_messages = []

    for user in users:
        last_message = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=user)) |
            (Q(receiver=request.user) & Q(sender=user))
        ).order_by('-timestamp').first()

        user_last_messages.append({
            'user': user,
            'last_message': last_message
        })

        groups=GroupChat.objects.all()
    # Sort user_last_messages by the timestamp of the last_message in descending order
    user_last_messages.sort(
       key=lambda x: x['last_message'].timestamp if x['last_message'] else None,
        reverse=True
    )

    return render(request, 'chat.html', {
        'room_name': room_name,
        'chats': chats,
        'group_chats': groups,
        'users': users,
        'user_last_messages': user_last_messages,
        'search_query': search_query 
    })

@login_required
def group_chat(request, group_name):
    """Handle group chat"""
    try:
        group = get_object_or_404(GroupChat, name=group_name)
        
        # Check if user is a member of the group
        if request.user not in group.members.all():
            return redirect('chat_list')
        
    except:
        return redirect('chat_list')
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get group messages
    messages_query = GroupMessage.objects.filter(group=group).order_by('timestamp')
    
    if search_query:
        messages_query = messages_query.filter(content__icontains=search_query)
    
    messages = messages_query
    
    # Get user last messages for sidebar
    user_last_messages = []
    users = User.objects.exclude(id=request.user.id)
    
    for user in users:
        last_message = Message.objects.filter(
            Q(sender=request.user, receiver=user) | 
            Q(sender=user, receiver=request.user)
        ).order_by('-timestamp').first()
        
        user_last_messages.append({
            'user': user,
            'last_message': last_message
        })
    
    # Sort by most recent message
    user_last_messages.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else timezone.now(), reverse=True)
    
    group_chats = GroupChat.objects.filter(members=request.user).annotate(
       last_message_time=Max('messages__timestamp')
     ).order_by('-last_message_time')
    # Add last message to each group
    for group_chat in group_chats:
        group_chat.last_message = GroupMessage.objects.filter(group=group_chat).order_by('-timestamp').first()
    
    context = {
        'room_name': group_name,
        'chats': messages,
        'user_last_messages': user_last_messages,
        'group_chats': group_chats,
        'is_group_chat': True,
        'member_count': group.members.count(),
        'search_query': search_query,
        'slug': group_name,
    }
    
    return render(request, 'chat.html', context)