from flask import Blueprint, render_template, session, redirect, request, url_for
from app.services.user_service import UserService
from app.services.post_service import PostService
from app.utils.decorators import login_required
from app.models.notification import Notification
from app import db

dashboard_bp = Blueprint('dashboard', __name__)
user_service = UserService()
post_service = PostService()

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    current_user = user_service.get_by_id(session['user_id'])
    stats = post_service.get_user_stats(session['user_id'])
    recent_activities = post_service.get_recent_activities()
    
    return render_template(
        "dashboard.html",
        user=current_user,
        user_posts_count=stats['total_posts'],
        lost_items_count=stats['lost_items'],
        found_items_count=stats['found_items'],
        recent_activities=recent_activities
    )

@dashboard_bp.route("/notifications/mark-read/<int:notification_id>")
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id == session['user_id']:
        notification.is_read = True
        db.session.commit()
    return redirect(notification.link)

@dashboard_bp.route("/notifications/clear-all")
@login_required
def clear_notifications():
    # Only delete notifications, don't just mark them as read
    Notification.query.filter_by(user_id=session['user_id']).delete()
    db.session.commit()
    return redirect(request.referrer or url_for('dashboard.dashboard'))
