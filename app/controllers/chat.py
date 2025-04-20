from flask import Blueprint, render_template, session, jsonify, request
from app.models.chat import Chat
from app.models.verificationClaim import VerificationClaim
from app.models.post import Post
from app.models.user import User
from app.utils.decorators import login_required
from app import db
from sqlalchemy import or_, and_
from datetime import datetime

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/messages')
@login_required
def messages():
    # Get all posts where the user has approved verification claims
    verified_posts = db.session.query(Post).join(VerificationClaim).filter(
        VerificationClaim.user_id == session['user_id'],
        VerificationClaim.status == 'approved'
    ).all()

    # Get all posts owned by the user that have approved claims
    owned_posts = db.session.query(Post).join(VerificationClaim).filter(
        Post.user_id == session['user_id'],
        VerificationClaim.status == 'approved'
    ).all()

    # Combine all relevant posts
    all_relevant_posts = verified_posts + owned_posts

    return render_template('chat/messages.html', posts=all_relevant_posts)

@chat_bp.route('/conversation/<int:post_id>')
@login_required
def conversation(post_id):
    post = Post.query.get_or_404(post_id)

    # Verify that the current user is either the post owner or has an approved claim
    is_owner = post.user_id == session['user_id']
    has_approved_claim = VerificationClaim.query.filter_by(
        post_id=post_id,
        user_id=session['user_id'],
        status='approved'
    ).first() is not None

    if not (is_owner or has_approved_claim):
        return jsonify({'error': 'Unauthorized'}), 403

    # Get the other user's ID (if owner, get claimer; if claimer, get owner)
    other_user_id = post.user_id if not is_owner else VerificationClaim.query.filter_by(
        post_id=post_id,
        status='approved'
    ).first().user_id

    # Get chat messages
    messages = Chat.query.filter(
        Chat.post_id == post_id,
        or_(
            and_(Chat.sender_id == session['user_id'], Chat.receiver_id == other_user_id),
            and_(Chat.sender_id == other_user_id, Chat.receiver_id == session['user_id'])
        )
    ).order_by(Chat.created_at).all()

    # Mark unread messages as read
    unread_messages = Chat.query.filter_by(
        post_id=post_id,
        receiver_id=session['user_id'],
        is_read=False
    ).all()

    for message in unread_messages:
        message.is_read = True
    db.session.commit()

    other_user = User.query.get(other_user_id)

    return render_template('chat/conversation.html',
                         messages=messages,
                         post=post,
                         other_user=other_user)

@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    post_id = request.form.get('post_id')
    message_text = request.form.get('message')
    receiver_id = request.form.get('receiver_id')

    if not all([post_id, message_text, receiver_id]):
        return jsonify({'error': 'Missing required fields'}), 400

    post = Post.query.get_or_404(post_id)

    # Verify that the current user is either the post owner or has an approved claim
    is_owner = post.user_id == session['user_id']
    has_approved_claim = VerificationClaim.query.filter_by(
        post_id=post_id,
        user_id=session['user_id'],
        status='approved'
    ).first() is not None

    if not (is_owner or has_approved_claim):
        return jsonify({'error': 'Unauthorized'}), 403

    message = Chat(
        post_id=post_id,
        sender_id=session['user_id'],
        receiver_id=receiver_id,
        message=message_text
    )

    db.session.add(message)
    db.session.commit()

    return jsonify({
        'id': message.id,
        'message': message.message,
        'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'sender_name': message.sender.name
    })

@chat_bp.route('/check_new_messages/<int:post_id>/<timestamp>')
@login_required
def check_new_messages(post_id, timestamp):
    post = Post.query.get_or_404(post_id)

    # Convert timestamp to datetime
    last_check = datetime.fromtimestamp(int(timestamp))

    # Verify that the current user is either the post owner or has an approved claim
    is_owner = post.user_id == session['user_id']
    has_approved_claim = VerificationClaim.query.filter_by(
        post_id=post_id,
        user_id=session['user_id'],
        status='approved'
    ).first() is not None

    if not (is_owner or has_approved_claim):
        return jsonify({'error': 'Unauthorized'}), 403

    # Get the other user's ID
    other_user_id = post.user_id if not is_owner else VerificationClaim.query.filter_by(
        post_id=post_id,
        status='approved'
    ).first().user_id

    # Get new messages
    new_messages = Chat.query.filter(
        Chat.post_id == post_id,
        Chat.created_at > last_check,
        or_(
            and_(Chat.sender_id == session['user_id'], Chat.receiver_id == other_user_id),
            and_(Chat.sender_id == other_user_id, Chat.receiver_id == session['user_id'])
        )
    ).all()

    # Mark messages as read
    unread_messages = [msg for msg in new_messages if msg.receiver_id == session['user_id']]
    for message in unread_messages:
        message.is_read = True
    db.session.commit()

    return jsonify({
        'messages': [{
            'id': msg.id,
            'message': msg.message,
            'sender_id': msg.sender_id,
            'created_at': msg.created_at.strftime('%H:%M')
        } for msg in new_messages]
    })
