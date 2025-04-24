from app.repositories.chat_repository import ChatRepository
from app.repositories.post_repository import PostRepository
from app.repositories.verification_repository import VerificationRepository
from app.models.chat import Chat
from app.models.message import Message
from sqlalchemy import or_, and_
from app import db

class ChatService:
    def __init__(self):
        self.chat_repository = ChatRepository()
        self.post_repository = PostRepository()
        self.verification_repository = VerificationRepository()

    def get_user_chats(self, user_id):
        return self.chat_repository.get_user_chats(user_id)

    def get_conversation(self, post_id, user_id):
        # Get post first
        post = self.post_repository.get_by_id(post_id)

        # Get messages and chat
        messages, chat = self.chat_repository.get_conversation(post_id, user_id)

        if not chat:
            raise ValueError("Chat not found")

        # Determine other user from chat object
        other_user = chat.sender if chat.sender_id != user_id else chat.receiver

        return messages, post, other_user

    def send_message(self, post_id, sender_id, receiver_id, message_content):
        if not all([post_id, sender_id, receiver_id, message_content]):
            raise ValueError("Missing required fields")

        # First get or create chat
        chat = Chat.query.filter(
            Chat.post_id == post_id,
            or_(
                and_(Chat.sender_id == sender_id, Chat.receiver_id == receiver_id),
                and_(Chat.sender_id == receiver_id, Chat.receiver_id == sender_id)
            )
        ).first()

        if not chat:
            chat = Chat(
                post_id=post_id,
                sender_id=sender_id,
                receiver_id=receiver_id
            )
            db.session.add(chat)
            db.session.commit()

        # Then create message
        return self.chat_repository.save_message(chat.id, message_content)

    def mark_messages_read(self, messages):
        return self.chat_repository.mark_messages_read(messages)

    def get_new_messages(self, post_id, user_id, timestamp):
        """Get messages newer than the given timestamp"""
        post = self.post_repository.get_by_id(post_id)
        if not post:
            raise ValueError("Post not found")

        is_owner = post.user_id == user_id
        has_approved_claim = self.verification_repository.has_approved_claim(post_id, user_id)
        is_lost_item = post.type == 'lost'

        if not (is_owner or has_approved_claim or is_lost_item):
            raise ValueError("Unauthorized access")

        return self.chat_repository.get_new_messages(post_id, timestamp)
