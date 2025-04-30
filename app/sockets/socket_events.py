from flask import session
from flask_socketio import emit, join_room, leave_room
from app.models.chat import Chat
from app.services.chat_service import ChatService
from app import socketio, db
from datetime import datetime

@socketio.on('join')
def on_join(data):
    room = f"post_{data['post_id']}"
    join_room(room)

@socketio.on('leave')
def on_leave(data):
    room = f"post_{data['post_id']}"
    leave_room(room)

@socketio.on('mark_read')
def on_mark_read(data):
    room = f"post_{data['post_id']}"
    socketio.emit('messages_read', {
        'post_id': data['post_id'],
        'reader_id': session['user_id']
    }, room=room)

@socketio.on('message')
def handle_message(data):
    if not session.get('user_id'):
        return

    if not ChatService.can_access_chat(session['user_id'], data['post_id']):
        return

    message = Chat(
        post_id=data['post_id'],
        sender_id=session['user_id'],
        receiver_id=data['receiver_id'],
        message=data['message']
    )

    db.session.add(message)
    db.session.commit()

    room = f"post_{data['post_id']}"
    emit('message', {
        'id': message.id,
        'sender_id': message.sender_id,
        'message': message.message,
        'created_at': message.created_at.strftime('%H:%M')
    }, room=room)
