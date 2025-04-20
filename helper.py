
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
        return url_for('static', filename='images/profile-pictures/default.png')

    return url_for('routes.profile_pictures', filename=f'{user.user_id}/{user.user_picture}')


def create_game_slider():
    supported_image_types = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    supported_video_types = ('.mp4', '.webm', '.ogg')

    folder = "static/images/games"
    media_files = []


    if not os.path.exists(folder):
        return media_files

    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)

        if not os.path.isfile(filepath):
            continue

        ext = filename.lower()
        if ext.endswith(supported_image_types):
            media_type = "image"
        elif ext.endswith(supported_video_types):
            media_type = "video"
        else:
            continue

        media_files.append({
            "url": f"/static/images/games/{filename}",
            "type": media_type
        })

    return media_files