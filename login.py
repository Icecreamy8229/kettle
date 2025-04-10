from flask_login import LoginManager
from models import db, User
from flask import redirect, url_for, flash
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    """
    This is how all unauthorized users will be handled.
    redirected to the login page.
    :return:
    """
    flash("please login first", "danger")
    return redirect(url_for("routes.login_route"))