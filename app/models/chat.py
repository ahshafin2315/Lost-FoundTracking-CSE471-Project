from app import db
from datetime import datetime

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    # Relationships
    post = db.relationship('Post', backref='chats')
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_chats')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_chats')
