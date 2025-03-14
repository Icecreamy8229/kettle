from mailer import mail
import yaml
import jinja2
from flask_mail import Message
from models import User
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import url_for, flash
import logging

with open("config.yaml") as f:
    config = yaml.safe_load(f)

SECRET_KEY = config['mailer']["secret_key"]
SECURITY_SALT = config['mailer']["salt"]

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt=SECURITY_SALT)



def send_verify_email(user: User):
    token = generate_verification_token(user.user_email)
    verification_url = url_for("routes.verify_email", token=token, _external=True)
    html_template = jinja2.Template(open("templates/eml_verify.html").read())

    msg = Message(
        subject="Kettle Email Verification",
        recipients=[user.user_email],
        html=html_template.render(user=user, verification_url=verification_url),
        sender=("Team Kettle", config['mailchimp']["username"])
    )
    mail.send(msg)
    logging.info("Sent verification email to %s", user.user_email)


def verify_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt=SECURITY_SALT, max_age=expiration)
        return email
    except SignatureExpired:
        flash("Verification link has expired. Please request a new one.", "error")
        return None
    except BadSignature:
        flash("Invalid or tampered verification link.", "error")
        return None