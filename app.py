from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lostandfound.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "dev_secret_key" 
app.config["UPLOAD_FOLDER"] = "static/uploads"
db = SQLAlchemy(app)

# Basic Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(200))
    type = db.Column(db.String(50)) # lost or found
    status = db.Column(db.String(50), default='open')  # pending, closed
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Basic Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

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
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
