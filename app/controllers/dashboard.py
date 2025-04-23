from flask import Blueprint, render_template, session, redirect, request, url_for, flash
from app.services.dashboard_service import DashboardService
from app.services.user_service import UserService
from app.utils.decorators import login_required

dashboard_bp = Blueprint("dashboard", __name__)
dashboard_service = DashboardService()
user_service = UserService()


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    current_user = user_service.get_by_id(session["user_id"])
    stats = dashboard_service.get_user_stats(session["user_id"])
    recent_activities = dashboard_service.get_recent_activities()
    top_contributors = dashboard_service.get_top_contributors()

    return render_template(
        "dashboard.html",
        user=current_user,
        user_posts_count=stats["total_posts"],
        lost_items_count=stats["lost_items"],
        found_items_count=stats["found_items"],
        recent_activities=recent_activities,
        top_contributors=top_contributors,
    )


@dashboard_bp.route("/notifications/mark-read/<int:notification_id>")
@login_required
def mark_notification_read(notification_id):
    try:
        notification = dashboard_service.mark_notification_read(
            notification_id, session["user_id"]
        )
        return redirect(notification.link)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/notifications/clear-all")
@login_required
def clear_notifications():
    dashboard_service.clear_user_notifications(session["user_id"])
    return redirect(request.referrer or url_for("dashboard.dashboard"))
