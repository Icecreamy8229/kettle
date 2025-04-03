
from models import User
from flask import url_for
"""
Using this module to help you create dummy users for now.
I may add other functions here in the future if we need other ways to generate content
outside of the website.

Right now it just generates dummy users in your database.

You use it this way:

py helper.py "testuser" "testuser@gmail.com" "password123!"
"""




def get_profile_picture(user: User) -> str:

    if user.user_picture == "default.png" or not user.user_picture:
        return url_for('static', filename='profile-pictures/default.png')

    return url_for('routes.profile_pictures', filename=f'{user.user_id}/{user.user_picture}')

