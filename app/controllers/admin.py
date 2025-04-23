from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from app.services.user_service import UserService
from app.services.post_service import PostService
from app.utils.decorators import admin_required
from app.models.user import User
from app.models.post import Post
from app.models.user_report import UserReport
from app import db
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__)
user_service = UserService()
post_service = PostService()

@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_banned=False).count(),
        'admin_users': User.query.filter_by(is_admin=True).count(),
        'total_posts': Post.query.count(),
        'pending_reports': UserReport.query.filter_by(status='pending').count(),
        'total_reports': UserReport.query.count()
    }
    
    recent_reports = UserReport.query.order_by(UserReport.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', stats=stats, 
                         recent_reports=recent_reports, recent_users=recent_users)

@admin_bp.route("/users")
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route("/reports")
@admin_required
def manage_reports():
    # Get filter parameters
    category = request.args.get('category', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    location = request.args.get('location', '')
    status = request.args.get('status', '')
    report_type = request.args.get('type', '')
    
    # Base query
    query = Post.query
    
    # Apply filters
    if category:
        query = query.filter(Post.category_name == category)
    if location:
        query = query.filter(Post.location.ilike(f'%{location}%'))
    if status:
        query = query.filter(Post.status == status)
    if report_type:
        query = query.filter(Post.type == report_type)
    if date_from:
        query = query.filter(Post.post_date >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Post.post_date <= datetime.strptime(date_to, '%Y-%m-%d'))
        
    posts = query.order_by(Post.post_date.desc()).all()
    user_reports = UserReport.query.order_by(UserReport.created_at.desc()).all()
    
    return render_template('admin/reports.html', 
                         posts=posts,
                         user_reports=user_reports,
                         filters={
                             'category': category,
                             'date_from': date_from,
                             'date_to': date_to,
                             'location': location,
                             'status': status,
                             'type': report_type
                         })

@admin_bp.route("/report/<int:report_id>/delete", methods=['POST'])
@admin_required
def delete_report(report_id):
    report = UserReport.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    flash("Report deleted successfully", "success")
    return redirect(url_for('admin.manage_reports'))

@admin_bp.route("/user/<int:user_id>/toggle-ban", methods=['POST'])
@admin_required
def toggle_user_ban(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = not user.is_banned
    db.session.commit()
    flash(f"User {'banned' if user.is_banned else 'unbanned'} successfully", "success")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route("/report/<int:report_id>/resolve", methods=['POST'])
@admin_required
def resolve_report(report_id):
    report = UserReport.query.get_or_404(report_id)
    action = request.form.get('action')
    if action in ['approve', 'reject']:
        report.status = action
        db.session.commit()
        flash(f"Report {action}ed successfully", "success")
    return redirect(url_for('admin.manage_reports'))

@admin_bp.route("/post/<int:post_id>/update-status", methods=['POST'])
@admin_required
def update_post_status(post_id):
    post = Post.query.get_or_404(post_id)
    status = request.form.get('status')
    if status in ['active', 'resolved', 'hidden', 'flagged']:
        post.status = status
        db.session.commit()
        flash(f"Post status updated to {status}", "success")
    return redirect(url_for('admin.manage_reports'))

@admin_bp.route("/post/<int:post_id>/edit", methods=['GET', 'POST'])
@admin_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        try:
            # Update all possible fields
            post.item_name = request.form.get('item_name')
            post.description = request.form.get('description')
            post.category_name = request.form.get('category')
            post.location = request.form.get('location')
            post.contact_method = request.form.get('contact_method')
            post.type = request.form.get('type')
            
            # Handle date fields
            lost_found_date = request.form.get('lost_found_date')
            if lost_found_date:
                post.lOrF_date = datetime.strptime(lost_found_date, '%Y-%m-%d')

            # Handle image upload
            if 'images' in request.files:
                files = request.files.getlist('images')
                image_filenames = []
                for file in files:
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                        image_filenames.append(unique_filename)
                if image_filenames:
                    post.images = ','.join(image_filenames)

            db.session.commit()
            flash("Post updated successfully", "success")
            return redirect(url_for('admin.manage_reports'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating post: {str(e)}", "danger")
    return render_template('admin/edit_post.html', post=post)

@admin_bp.route("/post/<int:post_id>/delete", methods=['POST'])
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully", "success")
    return redirect(url_for('admin.manage_reports'))