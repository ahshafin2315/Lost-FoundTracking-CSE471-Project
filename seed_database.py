from app import app, db
from app.models.user import User
from app.models.post import Post
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import faker

fake = faker.Faker()

# Categories for posts
CATEGORIES = [
    "Electronics", "Books", "Clothing", "Documents",
    "Accessories", "Bags", "Keys", "Wallets"
]

# Common locations
LOCATIONS = [
    "Library", "Student Center", "Cafeteria", "Gymnasium",
    "Parking Lot", "Academic Building", "Dormitory", "Campus Ground"
]

def create_sample_users(count=20):
    print(f"Creating {count} sample users...")
    users = []

    for i in range(count):
        user = User(
            name=fake.name(),
            email=f"user{i+1}@example.com",
            password=generate_password_hash("password123"),
            contact_info=fake.phone_number(),
            is_admin=False,
            contribution=random.randint(0, 10)
        )
        db.session.add(user)
        users.append(user)

    db.session.commit()
    return users

def create_sample_posts(users, count=50):
    print(f"Creating {count} sample posts...")
    current_date = datetime.utcnow()

    for i in range(count):
        user = random.choice(users)
        is_lost = random.choice([True, False])
        post_date = current_date - timedelta(days=random.randint(0, 30))
        incident_date = post_date - timedelta(days=random.randint(1, 5))

        post = Post(
            user_id=user.id,
            type="lost" if is_lost else "found",
            category_name=random.choice(CATEGORIES),
            item_name=f"{random.choice(['Blue', 'Black', 'Red', 'White'])} {random.choice(CATEGORIES)}",
            description=fake.text(max_nb_chars=200),
            location=random.choice(LOCATIONS),
            post_date=post_date,
            lOrF_date=incident_date,
            status=True,
            contact_method=random.choice(["Email", "Phone", "WhatsApp"]),
            verification_status=random.choice(["pending", "verified"]),
            share_count=random.randint(0, 20)
        )
        db.session.add(post)

    db.session.commit()

def seed_database():
    with app.app_context():
        # Clear existing data
        print("Clearing existing data...")
        db.session.query(Post).delete()
        db.session.query(User).delete()
        db.session.commit()

        # Create new data
        users = create_sample_users(20)
        create_sample_posts(users, 50)

        print("Database seeding completed!")

if __name__ == "__main__":
    seed_database()
