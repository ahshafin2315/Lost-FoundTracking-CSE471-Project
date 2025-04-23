from app.repositories.user_repository import UserRepository
from app.repositories.post_repository import PostRepository
from app.repositories.notification_repository import NotificationRepository

class DashboardService:
    def __init__(self):
        self.user_repository = UserRepository()
        self.post_repository = PostRepository()
        self.notification_repository = NotificationRepository()

    def get_user_stats(self, user_id):
        return {
            'total_posts': self.post_repository.count_user_posts(user_id),
            'lost_items': self.post_repository.count_user_posts(user_id, 'lost'),
            'found_items': self.post_repository.count_user_posts(user_id, 'found')
        }

    def get_top_contributors(self, limit=5):
        return self.user_repository.get_top_contributors(limit)

    def get_recent_activities(self, limit=9):
        return self.post_repository.get_recent_posts(limit)

    def mark_notification_read(self, notification_id, user_id):
        return self.notification_repository.mark_read(notification_id, user_id)

    def clear_user_notifications(self, user_id):
        return self.notification_repository.clear_all(user_id)
