from flask import Flask
from routes import routes
import yaml


#initializes our app and tells it where to look for html pages.
app = Flask(__name__, template_folder='templates')

#registers our endpoints.  "/" being the index page.
app.register_blueprint(routes)


with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

#this if statement just checks that you are running main.py, rather than an import
if __name__ == '__main__':

    if config['environment'] == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True)



