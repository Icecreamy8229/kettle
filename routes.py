from flask import render_template, Blueprint
import logging
import random

routes = Blueprint('routes', __name__) #this module points to itself for routes.

@routes.route('/') #This is the general syntax for creating a route in flask.
def index_route():
    logging.debug('Index route called')
    random_number = random.randint(0, 9)  #we can remove, just showing an example of template tags.
    return render_template('index.html', random_number=str(random_number))


@routes.route('/game') #this will be modified later, but adding so we can hit the game page url for now.
def game_route():
    logging.debug('Game route called')
    return render_template('game.html')


@routes.route('/user')
def user_route():
    logging.debug('User route called')
    return render_template('user.html')