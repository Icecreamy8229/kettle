from flask import render_template, Blueprint, session, request, redirect, url_for, flash
import logging
import random
from models import db, User
from flask_login import LoginManager, login_required, login_user
from login import load_user

routes = Blueprint('routes', __name__)  # this module points to itself for routes.


@routes.route('/')  # This is the general syntax for creating a route in flask.
def index_route():
    logging.debug('Index route called')
    return render_template('index.html')


@routes.route('/game')  # this will be modified later, but adding so we can hit the game page url for now.
def game_route():
    logging.debug('Game route called')
    return render_template('game.html')


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
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        user = db.session.query(User).filter_by(username=username).first()
        if user and user.verify_password(password):
            login_user(user)
            return redirect(url_for("index_route"))

        flash("Invalid username or password", "danger")


@routes.route("/logout")
@login_required
def logout_route():
    pass