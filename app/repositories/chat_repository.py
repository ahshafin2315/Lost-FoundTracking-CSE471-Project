from app.models.chat import Chat
from app.models.post import Post
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
        return Chat.query.filter(
            Chat.post_id == post_id,
            or_(
                Chat.sender_id == user_id,
                Chat.receiver_id == user_id
            )
        ).order_by(Chat.created_at).all()

    def save(self, chat):
        db.session.add(chat)
        db.session.commit()
        return chat

    def mark_messages_read(self, messages):
        for message in messages:
            message.is_read = True
        db.session.commit()

    def get_new_messages(self, post_id, timestamp):
        """Get messages newer than the given timestamp"""
        timestamp_dt = datetime.fromtimestamp(timestamp)
        return Chat.query.filter(
            Chat.post_id == post_id,
            Chat.created_at > timestamp_dt
        ).order_by(Chat.created_at).all()
