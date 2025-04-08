from flask import Flask, render_template, session, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lostandfound.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "dev_secret_key"
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)


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
    if "user_id" in session:
        return redirect(url_for("lost_items"))
        
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
            return redirect(url_for("lost_items"))
        
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
    return redirect(url_for("lost_items"))

@app.route("/lost-items")
@login_required
def lost_items():
    lost_items = Post.query.filter_by(type="lost").order_by(Post.date.desc()).all()
    return render_template("lost_items.html", items=lost_items)


# Create tables
with app.app_context():
    print("Creating database tables...")  # Debugging
    db.create_all()
    print("Database tables created.")  # Debugging

if __name__ == "__main__":
    app.run(debug=True)
