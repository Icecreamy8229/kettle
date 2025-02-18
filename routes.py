from flask import render_template, Blueprint
import logging

routes = Blueprint('routes', __name__) #this module points to itself for routes.

@routes.route('/') #This is the general syntax for creating a route in flask.
def index():
    logging.debug('Index route called')
    return render_template('index.html')