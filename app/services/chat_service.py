from app.models.chat import Chat
from app.models.post import Post
from app.models.verificationClaim import VerificationClaim
from app import db
from sqlalchemy import or_, and_

class ChatService:
    @staticmethod
    def get_post_chats(post_id, user_id):
        return Chat.query.filter(
            Chat.post_id == post_id,
            or_(Chat.sender_id == user_id, Chat.receiver_id == user_id)
        ).order_by(Chat.created_at).all()

    @staticmethod
    def get_inbox_items(user_id):
        # Get all posts where the user has chats
        posts_with_chats = db.session.query(Post).join(Chat).filter(
            or_(Chat.sender_id == user_id, Chat.receiver_id == user_id)
        ).distinct().all()

        # Split posts into owned and other posts
        owned_posts = []
        other_posts = []

        for post in posts_with_chats:
            if post.user_id == user_id:
                owned_posts.append(post)
            else:
                other_posts.append(post)

        return {
            'owned_posts': owned_posts,
            'other_posts': other_posts
        }

    @staticmethod
    def can_access_chat(user_id, post_id):
        post = Post.query.get(post_id)
        if not post:
            return False

        # If it's a lost item post, anyone can chat
        if post.type == 'lost':
            return True

        # If user owns the post
        if post.user_id == user_id:
            return True

        # For found items, check verification status
        if post.type == 'found':
            claim = VerificationClaim.query.filter_by(
                post_id=post_id,
                user_id=user_id,
                status='approved'
            ).first()
            return claim is not None

        return False

    @staticmethod
    def get_unread_count(user_id):
        return Chat.query.filter_by(receiver_id=user_id, is_read=False).count()

    @staticmethod
    def mark_messages_read(post_id, user_id):
        return Chat.mark_messages_read(post_id, user_id)
