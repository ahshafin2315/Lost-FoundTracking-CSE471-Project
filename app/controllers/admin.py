from flask import Blueprint, render_template, flash, redirect, url_for, request
from app.services.user_service import UserService
from app.services.post_service import PostService
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
user_service = UserService()
post_service = PostService()

@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    users = user_service.get_all_users()
    posts = post_service.get_recent_activities(10)
    # return render_template(
    #     "admin/dashboard.html",
    # )

@admin_bp.route("/users")
@admin_required
def manage_users():
    # Get all users from the database
    pass

@admin_bp.route("/posts")
@admin_required
def manage_posts():
    # Get all posts from the database
    pass