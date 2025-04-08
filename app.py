from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from auth_routes import auth  # Import the auth blueprint
from models import db, User, Post  # Import from models.py

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lostandfound.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "dev_secret_key"
app.config["UPLOAD_FOLDER"] = "static/uploads"
db.init_app(app)  # Initialize the database with the app

# Register the auth blueprint
app.register_blueprint(auth)

# Basic Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/lost-items')
def lost_items():
    return render_template('lost_items.html')

@app.route('/found-items')
def found_items():
    return render_template('found_items.html')

@app.route('/post/new')
def new_post():
    return render_template('new_post.html')

@app.route('/search')
def search():
    return render_template('search.html')

# Create tables
# Ensure tables are created
with app.app_context():
    print("Creating database tables...")  # Debugging
    db.create_all()
    print("Database tables created.")  # Debugging

if __name__ == '__main__':
    app.run(debug=True)
