from flask import Flask
from routes import routes
from login import login_manager
import yaml
import logging.config
from models import db
from secret import secret_key

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

logging.config.dictConfig(config["logging"])


#initializes our app and tells it where to look for html pages.
app = Flask(__name__, template_folder='templates')


#make sure the correct info is filled out in your config.yaml for how you have your database setup, or it will fail
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{config['database']['username']}:{config['database']['password']}@{config['database']['host']}/{config['database']['schema']}"
logging.debug("Configured database url %s", app.config["SQLALCHEMY_DATABASE_URI"])

app.secret_key = secret_key
db.init_app(app)
login_manager.init_app(app)

#registers our endpoints.  "/" being the index page.
app.register_blueprint(routes)






#this if statement just checks that you are running main.py, rather than an import
if __name__ == '__main__':

    if config['environment'] == 'production':
        app.run(debug=False, port=4999)
    else:
        app.run(debug=True)



