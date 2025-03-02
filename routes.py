from flask import render_template, Blueprint, session, request, redirect, url_for, flash
import logging
import random
from models import db, User
from flask_login import LoginManager, login_required, login_user, current_user
from login import load_user

routes = Blueprint('routes', __name__)  # this module points to itself for routes.


@routes.route('/')  # This is the general syntax for creating a route in flask.
def index_route():
    logging.debug('Index route called')
    return render_template('index.html')


@routes.route('/store')  # this will be modified later, but adding so we can hit the game page url for now.
def store_route():
    logging.debug('Game route called')
    return render_template('store.html')


@routes.route('/user')
def user_route():
    logging.debug('User route called')
    return render_template('user.html')

@routes.route('/testing')
def testing_route():
    return render_template('index.html')  #used for testing purposes.  when I need to test certain things I throw it under this route.

@routes.route("/settings")
@login_required
def settings_route():
    pass


@routes.route("/login", methods=['GET', 'POST'])
def login_route():

    if current_user.is_authenticated: #no need for an authenticated logged in user to get to this page.
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
            logging.info(f"Invalid username or password, attempted login: {user.user_login}")
            flash("Invalid username or password", "danger")

    return render_template('login.html')


@routes.route("/logout")
@login_required
def logout_route():
    pass