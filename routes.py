from flask import render_template, Blueprint
import logging
import random
from models import db, User

routes = Blueprint('routes', __name__) #this module points to itself for routes.

@routes.route('/') #This is the general syntax for creating a route in flask.
def index_route():
    logging.debug('Index route called')
    return render_template('index.html')


@routes.route('/game') #this will be modified later, but adding so we can hit the game page url for now.
def game_route():
    logging.debug('Game route called')
    return render_template('game.html')


@routes.route('/user')
def user_route():
    logging.debug('User route called')
    return render_template('user.html')

@routes.route('/testing')
def testing_route():
    new_user = User()
    new_user.user_email = "bigdog@gmail.com"
    new_user.user_login = "bigdog"
    new_user.user_alias = "bigdog"
    new_user.user_password = "smelly frogs1!"
    db.session.add(new_user)
    db.session.commit()
    return "hit"


