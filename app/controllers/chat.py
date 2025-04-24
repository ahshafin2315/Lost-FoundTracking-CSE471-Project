from flask import Blueprint, render_template, session, jsonify, request, flash, redirect, url_for
from app.services.chat_service import ChatService
from app.utils.decorators import login_required
from datetime import datetime

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')
chat_service = ChatService()

@chat_bp.route('/messages')
@login_required
def messages():
    my_posts, participating_posts = chat_service.get_user_chats(session['user_id'])
    return render_template('chat/messages.html',
                         my_posts=my_posts,
                         participating_posts=participating_posts)

@chat_bp.route('/conversation/<int:post_id>')
@login_required
def conversation(post_id):
    try:
        messages, post, other_user = chat_service.get_conversation(post_id, session["user_id"])
        chat_service.mark_messages_read(messages)
        return render_template(
            "chat/conversation.html",
            messages=messages,
            post=post,
            other_user=other_user
        )
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("chat.messages"))

@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    try:
        message = chat_service.send_message(
            post_id=request.form.get('post_id'),
            sender_id=session['user_id'],
            receiver_id=request.form.get('receiver_id'),
            message_content=request.form.get('message')  # Changed parameter name
        )
        return jsonify({
            'id': message.id,
            'message': message.content,  # Changed from message.message to message.content
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'sender_id': message.chat.sender_id  # Get sender_id through chat relationship
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@chat_bp.route("/conversation/<int:post_id>/messages")
@login_required
def check_new_messages(post_id):
    try:
        timestamp = request.args.get('timestamp', type=int)
        messages = chat_service.get_new_messages(post_id, session["user_id"], timestamp)
        return jsonify({
            'messages': [{
                'id': msg.id,
                'message': msg.message,
                'sender_id': msg.sender_id,
                'created_at': msg.created_at.strftime('%H:%M'),
            } for msg in messages]
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
