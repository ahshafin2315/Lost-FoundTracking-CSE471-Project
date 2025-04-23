from app.models.user import User
from app.models.post import Post
from app import db
from sqlalchemy import func

class UserRepository:
    @staticmethod
    def get_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def create(user):
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update(user):
        db.session.commit()
        return user

    def get_top_contributors(self, limit):
        return db.session.query(
            User,
            func.count(Post.id).label('post_count')
        ).join(Post).group_by(User.id)\
         .order_by(func.count(Post.id).desc())\
         .limit(limit).all()
