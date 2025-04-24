from app.models.chat import Chat
from app.models.post import Post
from app.models.message import Message
from sqlalchemy import or_, and_
from app import db
from datetime import datetime

class ChatRepository:
    def get_user_chats(self, user_id):
        my_posts = Post.query.filter(
            Post.user_id == user_id,
            Post.chats.any()
        ).all()

        participating_posts = Post.query.join(Chat).filter(
            Post.user_id != user_id,
            or_(
                Chat.sender_id == user_id,
                Chat.receiver_id == user_id
            )
        ).distinct().all()

        return my_posts, participating_posts

    def get_conversation(self, post_id, user_id):
        # First get the chat record
        chat = Chat.query.filter(
            Chat.post_id == post_id,
            or_(
                Chat.sender_id == user_id,
                Chat.receiver_id == user_id
            )
        ).first()

        if chat:
            # Then get all messages for this chat
            messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.created_at).all()
            return messages, chat
        return [], None

    def save(self, chat):
        db.session.add(chat)
        db.session.commit()
        return chat

    def save_message(self, chat_id, content):
        message = Message(chat_id=chat_id, content=content)
        db.session.add(message)
        db.session.commit()
        return message

    def mark_messages_read(self, messages):
        for message in messages:
            message.is_read = True
        db.session.commit()

    def get_new_messages(self, chat_id, timestamp):
        timestamp_dt = datetime.fromtimestamp(timestamp)
        return Message.query.filter(
            Message.chat_id == chat_id,
            Message.created_at > timestamp_dt
        ).order_by(Message.created_at).all()

    def get_first_message(self, post_id, user_id):
        """Get the first message for a given post and user"""
        chat = Chat.query.filter(
            Chat.post_id == post_id,
            or_(
                Chat.sender_id == user_id,
                Chat.receiver_id == user_id
            )
        ).first()

        if chat:
            # Get the first message for this chat ordered by creation date
            message = Message.query.filter_by(chat_id=chat.id).order_by(Message.created_at).first()
            return message

        return None
