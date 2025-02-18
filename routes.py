from flask import render_template, Blueprint
import logging
import random

routes = Blueprint('routes', __name__) #this module points to itself for routes.

@routes.route('/') #This is the general syntax for creating a route in flask.
def index():
    logging.debug('Index route called')
    random_number = random.randint(0, 9)  #we can remove, just showing an example of template tags.
    return render_template('index.html', random_number=str(random_number))


