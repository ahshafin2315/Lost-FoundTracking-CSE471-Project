from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User  # Import from models.py

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        print(f"Received data: Name={name}, Email={email}, Password={password}")  # Debugging

        hashed_password = generate_password_hash(password, method='sha256')
        print(f"Hashed password: {hashed_password}")  # Debugging

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            print("Email already registered.")  # Debugging
        else:
            try:
                new_user = User(name=name, email=email, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                print("User added to the database.")  # Debugging
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                print(f"Error adding user to the database: {e}")  # Debugging
                flash('An error occurred while registering. Please try again.', 'danger')
    return render_template('register.html')

@auth.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))