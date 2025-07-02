# chatApp/socketio_server.py
import socketio
import eventlet
import os
import sys
import django

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Setup Django - use the correct settings module name
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CodeAlpha_RealTimeCommunicationApp.settings')
django.setup()

# Create Socket.IO server
sio = socketio.Server(cors_allowed_origins="*")
app = socketio.WSGIApp(sio)

# Store connected users
connected_users = {}

@sio.event
def connect(sid, environ):
    print(f'Client {sid} connected')
    connected_users[sid] = {
        'connected_at': eventlet.util.now(),
        'ip': environ.get('REMOTE_ADDR', 'Unknown')
    }

@sio.event
def disconnect(sid):
    print(f'Client {sid} disconnected')
    if sid in connected_users:
        del connected_users[sid]

@sio.event
def join_room(sid, data):
    """Allow users to join specific chat rooms"""
    room = data.get('room', 'general')
    sio.enter_room(sid, room)
    sio.emit('status', {'message': f'Joined room: {room}'}, room=sid)
    print(f'Client {sid} joined room: {room}')

@sio.event
def leave_room(sid, data):
    """Allow users to leave specific chat rooms"""
    room = data.get('room', 'general')
    sio.leave_room(sid, room)
    sio.emit('status', {'message': f'Left room: {room}'}, room=sid)
    print(f'Client {sid} left room: {room}')

@sio.event
def message(sid, data):
    """Handle incoming messages"""
    room = data.get('room', 'general')
    message = data.get('message', '')
    username = data.get('username', f'User_{sid[:8]}')
    
    if message.strip():  # Only process non-empty messages
        message_data = {
            'message': message,
            'username': username,
            'sender_id': sid,
            'timestamp': eventlet.util.now(),
            'room': room
        }
        
        # Broadcast to all clients in the room
        sio.emit('new_message', message_data, room=room)
        print(f'Message in {room} from {username}: {message}')

@sio.event
def typing(sid, data):
    """Handle typing indicators"""
    room = data.get('room', 'general')
    username = data.get('username', f'User_{sid[:8]}')
    is_typing = data.get('typing', False)
    
    # Broadcast typing status to others in the room (exclude sender)
    sio.emit('user_typing', {
        'username': username,
        'typing': is_typing
    }, room=room, skip_sid=sid)

@sio.event
def get_online_users(sid, data):
    """Get list of online users"""
    room = data.get('room', 'general')
    room_users = []
    
    try:
        for user_sid in sio.manager.get_participants(sio.namespace, room):
            room_users.append({
                'id': user_sid,
                'username': f'User_{user_sid[:8]}'
            })
    except Exception as e:
        print(f"Error getting participants: {e}")
    
    sio.emit('online_users', {'users': room_users}, room=sid)

if __name__ == '__main__':
    print("Starting Socket.IO server on http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    try:
        eventlet.wsgi.server(eventlet.listen(('localhost', 8000)), app)
    except KeyboardInterrupt:
        print("\nSocket.IO server stopped")