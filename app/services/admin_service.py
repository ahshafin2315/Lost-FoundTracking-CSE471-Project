from app.repositories.user_repository import UserRepository
from app.repositories.post_repository import PostRepository
from app.models.user import User
from app.models.post import Post
from app.models.user_report import UserReport
from app import db

class AdminService:
    def __init__(self):
        self.user_repository = UserRepository()
        self.post_repository = PostRepository()

    def get_dashboard_stats(self):
        return {
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(is_banned=False).count(),
            'admin_users': User.query.filter_by(is_admin=True).count(),
            'total_posts': Post.query.count(),
            'pending_reports': UserReport.query.filter_by(status='pending').count()
        }

    def toggle_user_ban(self, user_id):
        user = User.query.get(user_id)
        if user:
            user.is_banned = not user.is_banned
            db.session.commit()
            return True
        return False

    def resolve_report(self, report_id, action):
        report = UserReport.query.get(report_id)
        if report and action in ['approve', 'reject']:
            report.status = action
            db.session.commit()
            return True
        return False