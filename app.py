from flask import Flask, render_template, session, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lostandfound.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "dev_secret_key"
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)


@app.context_processor
def inject_common_data():
    notifications = []  # You can implement actual notifications later
    notifications_count = len(notifications)
    return {
        'current_year': datetime.utcnow().year,
        'notifications': notifications,
        'notifications_count': notifications_count
    }


# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    contact_info = db.Column(db.String(200))
    posts = db.relationship("Post", backref="user", lazy=True)
    reported_by = db.relationship(
        "UserReport",
        foreign_keys="UserReport.reporter_id",
        backref="reporter",
        lazy=True,
    )
    reports_against = db.relationship(
        "UserReport",
        foreign_keys="UserReport.reported_user_id",
        backref="reported_user",
        lazy=True,
    )


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False)
    category_id = db.Column(db.Integer)
    category_name = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(200))
    images = db.Column(db.String(1000))
    status = db.Column(db.Boolean, default=True)
    share_count = db.Column(db.Integer, default=0)
    verification_status = db.Column(db.String(50), default="pending")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.String(50))


class UserReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class VerificationClaim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    status = db.Column(db.String(50), default="pending")
    proof_details = db.Column(db.String(1000))
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    verification_score = db.Column(db.Float, default=0.0)


# Authentication Routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if user.is_banned:
                flash("Your account has been suspended. Please contact admin.", "danger")
                return redirect(url_for("login"))
            
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["is_admin"] = user.is_admin
            session.permanent = True  # Make session persistent
            
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for("dashboard"))
        
        flash("Invalid email or password", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("lost_items"))
        
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        contact = request.form.get("contact_info", "")

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            contact_info=contact
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.", "danger")

    return render_template("register.html")

@app.route("/logout")
def logout():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_name = session.get("user_name", "User")
    session.clear()
    flash(f"Goodbye, {user_name}! You have been logged out.", "info")
    return redirect(url_for("login"))

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# Main Routes
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))

@app.route("/lost-items")
@login_required
def lost_items():
    lost_items = Post.query.filter_by(type="lost").order_by(Post.date.desc()).all()
    return render_template("lost_items.html", items=lost_items)

@app.route("/found-items")
@login_required
def found_items():
    found_items = Post.query.filter_by(type="found").order_by(Post.date.desc()).all()
    return render_template("found_items.html", items=found_items)

@app.route("/report-lost-item", methods=["GET", "POST"])
@login_required
def report_lost_item():
    if request.method == "POST":
        try:
            # Get form data
            category = request.form.get("category")
            item_name = request.form.get("item_name")
            lost_date = datetime.strptime(request.form.get("lost_date"), "%Y-%m-%d")
            place_lost = request.form.get("place_lost")
            contact_method = request.form.get("contact_method")
            contact_info = request.form.get("contact_info")
            
            # Handle image upload
            image_filename = None
            if "image" in request.files:
                image = request.files["image"]
                if image.filename != "":
                    try:
                        # Ensure uploads directory exists
                        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                        
                        # Generate unique filename
                        ext = image.filename.rsplit(".", 1)[1].lower()
                        image_filename = f"{uuid.uuid4()}.{ext}"
                        image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
                        image.save(image_path)
                        print(f"Image saved to: {image_path}")  # Debug logging
                    except Exception as img_error:
                        print(f"Image upload error: {img_error}")  # Debug logging
                        flash("Error uploading image. Report saved without image.", "warning")

            print(f"Creating post with data: {category}, {item_name}, {lost_date}")  # Debug logging

            # Create new post
            new_post = Post(
                category_name=category,
                description=f"Item Name: {item_name}\nContact Method: {contact_method}\nContact Info: {contact_info}",
                date=lost_date,
                location=place_lost,
                images=image_filename,
                type="lost",
                user_id=session["user_id"]
            )
            
            db.session.add(new_post)
            db.session.commit()
            print("Post saved successfully")  # Debug logging
            flash("Lost item reported successfully!", "success")
            return redirect(url_for("lost_items"))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error in report_lost_item: {str(e)}")  # Debug logging
            flash(f"Error reporting lost item: {str(e)}", "danger")
            
    return render_template("report_lost_item.html")

@app.route("/report-found-item", methods=["GET", "POST"])
@login_required
def report_found_item():
    if request.method == "POST":
        try:
            category = request.form.get("category")
            item_name = request.form.get("item_name")
            found_date = datetime.strptime(request.form.get("found_date"), "%Y-%m-%d")
            place_found = request.form.get("place_found")
            contact_method = request.form.get("contact_method")
            contact_info = request.form.get("contact_info")
            
            # Handle image upload
            image_filename = None
            if "image" in request.files:
                image = request.files["image"]
                if image.filename != "":
                    try:
                        # Ensure uploads directory exists
                        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                        
                        # Generate unique filename
                        ext = image.filename.rsplit(".", 1)[1].lower()
                        image_filename = f"{uuid.uuid4()}.{ext}"
                        image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
                        image.save(image_path)
                        print(f"Image saved to: {image_path}")  # Debug logging
                    except Exception as img_error:
                        print(f"Image upload error: {img_error}")  # Debug logging
                        flash("Error uploading image. Report saved without image.", "warning")

            print(f"Creating post with data: {category}, {item_name}, {found_date}")  # Debug logging

            # Create new post
            new_post = Post(
                category_name=category,
                description=f"Item Name: {item_name}\nContact Method: {contact_method}\nContact Info: {contact_info}",
                date=found_date,
                location=place_found,
                images=image_filename,
                type="found",
                user_id=session["user_id"]
            )
            
            db.session.add(new_post)
            db.session.commit()
            print("Post saved successfully")  # Debug logging
            flash("Found item reported successfully!", "success")
            return redirect(url_for("found_items"))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error in report_found_item: {str(e)}")  # Debug logging
            flash(f"Error reporting found item: {str(e)}", "danger")
            
    return render_template("report_found_item.html")

@app.route("/post/<int:post_id>")
@login_required
def view_post(post_id):
    # Get the post from database using post_id
    post = Post.query.get_or_404(post_id)
    
    # Get the post owner
    post_owner = User.query.get_or_404(post.user_id)
    
    # Check if current user is the owner
    is_owner = False
    if 'user_id' in session:
        is_owner = (session['user_id'] == post.user_id)
    
    return render_template("view_post.html", 
                         post=post,
                         post_owner=post_owner,
                         is_owner=is_owner)

@app.route("/dashboard")
@login_required 
def dashboard():
    # Get button actions
    action = request.args.get('action', '')
    if action == 'your_posts':
        return redirect(url_for('user_posts'))
    elif action == 'lost_items':
        return redirect(url_for('lost_items'))
    elif action == 'found_items':
        return redirect(url_for('found_items'))

    # Get search query
    search_query = request.args.get('search', '')
    
    # Get user stats
    user_posts = Post.query.filter_by(user_id=session['user_id']).all()
    user_posts_count = len(user_posts)
    lost_items_count = Post.query.filter_by(type="lost").count()
    found_items_count = Post.query.filter_by(type="found").count()
    
    # Get related posts based on user's post categories
    user_categories = [post.category_name for post in user_posts]
    related_posts = []
    
    if search_query:
        # If there's a search query, filter by description
        related_posts = Post.query.filter(
            Post.description.ilike(f'%{search_query}%')
        ).order_by(Post.date.desc()).limit(6).all()
    elif user_categories:
        # Otherwise show posts in same categories as user's posts
        related_posts = Post.query.filter(
            Post.category_name.in_(user_categories),
            Post.user_id != session['user_id']
        ).order_by(Post.date.desc()).limit(6).all()
    
    # Get recent activities (last 5 posts)
    recent_activities = Post.query.order_by(
        Post.date.desc()
    ).limit(5).all()
    
    return render_template(
        "dashboard.html",
        user_posts_count=user_posts_count,
        lost_items_count=lost_items_count,
        found_items_count=found_items_count,
        related_posts=related_posts,
        recent_activities=recent_activities
    )

@app.route("/user-posts")
@login_required
def user_posts():
    user_posts = Post.query.filter_by(user_id=session['user_id']).order_by(Post.date.desc()).all()
    return render_template("user_posts.html", posts=user_posts)

@app.route("/post/<int:post_id>")
@login_required
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("view_post.html", post=post)


# Create default users (test purposes only)
def create_default_users():
    # Check if default admin already exists
    if not User.query.filter_by(email="admin@test.com").first():
        admin = User(
            name="Admin User",
            email="admin@test.com",
            password=generate_password_hash("admin123"),
            is_admin=True,
            contact_info="Admin Contact"
        )
        db.session.add(admin)

    # Check if default regular user already exists
    if not User.query.filter_by(email="user@test.com").first():
        user = User(
            name="Test User",
            email="user@test.com",
            password=generate_password_hash("user123"),
            is_admin=False,
            contact_info="Test User Contact"
        )
        db.session.add(user)
    
    db.session.commit()

# Create tables
with app.app_context():
    print("Creating database tables...")
    db.create_all()
    create_default_users()
    print("Database tables and default users created.")

if __name__ == "__main__":
    app.run(debug=True)
