from app.models.notification import Notification
from app import db

class NotificationRepository:
    def get_user_notifications(self, user_id):
        return Notification.query.filter_by(user_id=user_id)\
            .order_by(Notification.created_at.desc()).all()

    def mark_read(self, notification_id, user_id):
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first_or_404()
        notification.is_read = True
        db.session.commit()
        return notification

    def clear_all(self, user_id):
        Notification.query.filter_by(user_id=user_id).delete()
        db.session.commit()
