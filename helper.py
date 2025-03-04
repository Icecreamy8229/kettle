import argparse

"""
Using this module to help you create dummy users for now.
I may add other functions here in the future if we need other ways to generate content
outside of the website.

Right now it just generates dummy users in your database.

You use it this way:

py helper.py "testuser" "testuser@gmail.com" "password123!"
"""

def main():
    parser = argparse.ArgumentParser(description="Helper script to create a dummy user.")
    parser.add_argument("username", type=str, help="A unique username")
    parser.add_argument("alias", type=str, help="This does not have to be unique")
    parser.add_argument("email", type=str, help="A unique email")
    parser.add_argument("password", type=str, help="password in plaintext, remember this!")
    args = parser.parse_args()
    create_dummy_user(username=args.username, alias=args.alias, email=args.email, plaintext_pass=args.password)


def create_dummy_user(username: str, alias: str, email: str, plaintext_pass: str):
    from main import app
    from models import User, db
    with app.app_context():
        user = User()
        user.user_login = username
        user.user_alias = alias
        user.password = plaintext_pass
        user.user_email = email
        db.session.add(user)
        db.session.commit()


if __name__ == '__main__':
    main()
