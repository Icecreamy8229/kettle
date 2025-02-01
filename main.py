from flask import Flask
from routes import routes

#initializes our app and tells it where to look for html pages.
app = Flask(__name__, template_folder='templates')

#registers our endpoints.  "/" being the index page.
app.register_blueprint(routes)



#this if statement just checks that you are running main.py, rather than an import
if __name__ == '__main__':
    app.run(debug=True)
