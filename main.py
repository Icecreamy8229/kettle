from flask import Flask
from routes import routes
from login import login_manager
import yaml
import logging.config
from models import db
from secret import secret_key
from helper import get_profile_picture
from mailer import mail

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

logging.config.dictConfig(config["logging"])


#initializes our app and tells it where to look for html pages.
app = Flask(__name__, template_folder='templates')

#This lets the get_profile_picture() function be usable in any html template.
app.jinja_env.globals['get_profile_picture'] = get_profile_picture

#make sure the correct info is filled out in your config.yaml for how you have your database setup, or it will fail
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{config['database']['username']}:{config['database']['password']}@{config['database']['host']}/{config['database']['schema']}"
logging.debug("Configured database url %s", app.config["SQLALCHEMY_DATABASE_URI"])


if config['environment'] == 'production':
    app.config['MAIL_SERVER'] = config['mailchimp']['url']
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = config['mailchimp']['username']
    app.config['MAIL_PASSWORD'] = config['mailchimp']['api_key']
    app.config['MAIL_DEFAULT_SENDER'] = (config['mailchimp']['username'], "Team Kettle")
    mail.init_app(app)

app.secret_key = secret_key
db.init_app(app)
login_manager.init_app(app)


#registers our endpoints.  "/" being the index page.
app.register_blueprint(routes)






#this if statement just checks that you are running main.py, rather than an import
if __name__ == '__main__':

    if config['environment'] == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True)



