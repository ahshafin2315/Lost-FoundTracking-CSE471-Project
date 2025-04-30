from flask import Blueprint, render_template, session, jsonify, request, flash, redirect, url_for
from app.models.post import Post
from app.models.user import User
from app.models.verificationClaim import VerificationClaim
from app.services.chat_service import ChatService
from app.utils.decorators import login_required
from app import db

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/inbox')
@login_required
def inbox():
    inbox_items = ChatService.get_inbox_items(session['user_id'])
    return render_template('chat/inbox.html',
                         owned_posts=inbox_items['owned_posts'],
                         other_posts=inbox_items['other_posts'])

@chat_bp.route('/messages')
@login_required
def messages():
    """Alias for inbox route for better semantics"""
    return inbox()

@chat_bp.route('/conversation/<int:post_id>')
@login_required
def conversation(post_id):
    if not ChatService.can_access_chat(session['user_id'], post_id):
        return jsonify({'error': 'Unauthorized access'}), 403

    post = Post.query.get_or_404(post_id)
    messages = ChatService.get_post_chats(post_id, session['user_id'])

    # Get the other user
    if post.user_id == session['user_id']:
        # If owner, get the claimer from verification claim
        if post.type == 'found':
            claim = VerificationClaim.query.filter_by(
                post_id=post_id,
                status='approved'
            ).first()
            other_user_id = claim.user_id if claim else None
        else:
            # For lost items, get latest chatter or None
            latest_chat = next((chat for chat in messages if chat.sender_id != session['user_id']), None)
            other_user_id = latest_chat.sender_id if latest_chat else None
    else:
        # If not owner, other user is always the post owner
        other_user_id = post.user_id

    other_user = User.query.get_or_404(other_user_id) if other_user_id else None
    if not other_user:
        flash('Could not determine chat participant', 'error')
        return redirect(url_for('posts.view_post', post_id=post_id))

    # Mark messages as read
    ChatService.mark_messages_read(post_id, session['user_id'])

    return render_template('chat/conversation.html',
                         post=post,
                         messages=messages,
                         other_user=other_user)
