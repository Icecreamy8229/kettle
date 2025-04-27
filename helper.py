from enum import Enum
import enum
from models import User, Game, Genre, GameGenre, db
from flask import url_for
import os
import logging

"""
Using this module to help you create dummy users for now.
I may add other functions here in the future if we need other ways to generate content
outside of the website.

Right now it just generates dummy users in your database.

You use it this way:

py helper.py "testuser" "testuser@gmail.com" "password123!"
"""


class SliderType(Enum):
    TAG = enum.auto()



def get_game_slider_media(slider_type: SliderType, tag_type=None):
    slider_display_images = []

    if slider_type == SliderType.TAG and tag_type is not None:

        tag = db.session.query(Genre).filter(Genre.genre_tag == tag_type).first()
        if tag:

            game_ids = (
                db.session.query(GameGenre.game_id)
                .filter(GameGenre.genre_id == tag.genre_id)
                .all()
            )
            game_ids = [game_id for (game_id,) in game_ids]


            games = db.session.query(Game).filter(Game.game_id.in_(game_ids)).all()


            for i, game in enumerate(games):
                if i >= 10:
                    break
                images = get_game_media("images", game)
                if images:
                    slider_display_images.append(images[0])

    return slider_display_images


def get_game_media(media_type, game: Game):
    media_files = []
    TOP_LEVEL_DIR = 'game_media'
    game_path = os.path.join(TOP_LEVEL_DIR, str(game.game_id))
    image_path = os.path.join(game_path, "images")
    video_path = os.path.join(game_path, "videos")

    if os.path.exists(image_path):
        for filename in os.listdir(image_path):
            file_url = f"/game_media/{game.game_id}/{media_type}/{filename}"
            if media_type == "images" and filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                media_files.append({"type": "image", "url": file_url})
            elif media_type == "videos" and filename.lower().endswith((".mp4", ".webm", ".ogg")):
                media_files.append({"type": "video", "url": file_url})

    if os.path.exists(video_path):
        for filename in os.listdir(video_path):
            file_url = f"/game_media/{game.game_id}/{media_type}/{filename}"
            if media_type == "images" and filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                media_files.append({"type": "image", "url": file_url})
            elif media_type == "videos" and filename.lower().endswith((".mp4", ".webm", ".ogg")):
                media_files.append({"type": "video", "url": file_url})

    if not os.path.exists(image_path):
        logging.warning(f"No image directory found for game_id {game.game_id}")

    return media_files

def get_profile_picture(user: User) -> str:

    if user.user_picture == "default.png" or not user.user_picture:
        return url_for('static', filename='images/profile-pictures/default.png')

    return url_for('routes.profile_pictures', filename=f'{user.user_id}/{user.user_picture}')


