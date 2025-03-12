import yaml
from flask import render_template, Blueprint, request, redirect, url_for, flash, jsonify
import logging
import random
from models import db, User, Cart, Game, Library
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from login import load_user
from email_utils import send_verify_email, verify_token

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
routes = Blueprint('routes', __name__)  # this module points to itself for routes.


@routes.route('/')  # This is the general syntax for creating a route in flask.
def index_route():
    logging.debug('Index route called')
    return render_template('index.html')

@routes.route('/checkout')
def checkout_route():
    logging.debug('Checkout route called')
    return render_template('checkout.html', title='Checkout')

@routes.route('/about')
def about_route():
    logging.debug('About route called')
    return render_template('about.html', title='About')


@login_required
@routes.route('/user')
def user_route():
    logging.debug('User route called')
    if current_user.is_authenticated:
        return render_template('user.html')
    else:
        return render_template('login.html', title='Login')

@login_required
@routes.route('/library')
def library_route():
    logging.debug('Library route called')
    if not current_user.is_authenticated:

        return render_template('login.html')
        
    library_items = db.session.query(Library).filter_by(user_id=current_user.user_id).all()
    game_ids = [i.game_id for i in library_items]
    games = db.session.query(Game).filter(Game.game_id.in_(game_ids)).all()
    logging.info(f"Library route called, with these items: {games}")
    return render_template("library.html", games=games)

@routes.route('/testing')
def testing_route():
    return render_template('index.html')  # used for testing purposes.  when I need to test certain things I throw it under this route.


@routes.route("/settings")
@login_required
def settings_route():
    pass


@routes.route("/game/")
def game_route():
    return render_template('game.html', user=current_user)


@routes.route("/login", methods=['GET', 'POST'])
def login_route():
    if current_user.is_authenticated:  # no need for an authenticated logged in user to get to this page.
        return redirect(url_for('routes.index_route'))

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        user = db.session.query(User).filter_by(user_login=username).first()
        if user and user.verify_password(password):
            logging.info(f"{user.user_login} has successfully logged in")
            login_user(user)
            flash(f'You are now logged in as {user.user_login}', "success")
            return redirect(url_for('routes.index_route'))

        else:
            logging.info(f"Invalid username or password, attempted login: {username}")
            flash("Invalid username or password", "danger")

    return render_template('login.html', title='Login')


@routes.route("/signup", methods=['POST'])
def signup_route(): #this is only used to process data from the form and sign the user up.
    #the logic is not done yet.
    #use helper.py to create users for dev environment
    if current_user.is_authenticated:
        return redirect(url_for('routes.index_route'))

    data = request.form
    print(data)
    alias = data.get('alias')
    user_login = data.get('username')
    password = data.get('password')
    confirm_password = data.get('password-confirm')
    email = data.get('email')
    if not user_login or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400

    existing_user = db.session.query(User).filter_by(user_login=user_login).first()
    existing_email = db.session.query(User).filter_by(user_email=email).first()
    if existing_user or existing_email:
        return jsonify({'error': 'User already exists'}), 400

    new_user = User()
    new_user.user_login = user_login
    new_user.user_email = email
    new_user.user_alias = alias
    new_user.password = password
    if config['environment'] != 'production':
        new_user.user_verified = True
    db.session.add(new_user)
    db.session.commit()
    if config['environment'] == 'production':
        send_verify_email(new_user)

    return jsonify({'message': 'User registered successfully', 'user_login': user_login})







@login_required
@routes.route("/cart")
def cart_route():
    if not current_user.is_authenticated:
        logging.info(f"Cart route called, but the user is not authenticated.")
        return redirect(url_for('routes.index_route'))

    cart_items = db.session.query(Cart).filter_by(user_id=current_user.user_id).all()
    game_ids = [i.game_id for i in cart_items]
    games = db.session.query(Game).filter(Game.game_id.in_(game_ids)).all()
    logging.info(f"Cart route called, with these items: {games}")
    return render_template("checkout.html", games=games)


@routes.route("/logout")
@login_required
def logout_route():
    logout_user()
    flash("You have been logged out", "success")
    return redirect(url_for('routes.index_route'))

@routes.route("/verify-email/<token>")
def verify_email(token):

    email = verify_token(token)
    if not email:
        return redirect("/")

    user = User.query.filter_by(user_email=email).first()
    if not user:
        flash("User not found.", "error")
        return redirect("/")

    user.user_verified = True  # Mark user as verified
    db.session.commit()

    flash("Your email has been verified!", "success")
    return redirect("/")