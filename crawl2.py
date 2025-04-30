import os
import re
import yaml
import random
import requests
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from models import Game, Genre, GameGenre, db
from main import app

from PIL import Image
from io import BytesIO




logging.basicConfig(level=logging.NOTSET)


games_added = 0
game_page_set = set()
master_tag_set = set()


with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

blacklisted_tags = config['crawler']['blacklisted_tags']


def load_user_profile():
    options = webdriver.FirefoxOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--headless")
    options.set_preference("browser.startup.page", 1)
    options.set_preference("browser.startup.homepage_override.mstone", "ignore")
    options.set_preference("network.http.connection-retry-timeout", 0)
    options.set_preference("network.http.keep-alive.timeout", 10)
    options.set_preference("network.http.max-persistent-connections-per-server", 10)
    options.set_preference("network.http.max-persistent-connections-per-proxy", 10)
    return options

def startup_marionette():
    options = load_user_profile()
    driver = webdriver.Firefox(options=options)
    return driver

# Media downloader
def download_file(source, game_id, media_type: str, name = None):
    if name:
        folder = "cover"
    else:
        folder = 'images' if media_type == 'image' else 'videos'

    save_path = f"game_media/{game_id}/{folder}/{os.path.basename(source.split('?')[0])}"

    if name == "cover":
        name = "cover.png"
        save_path = f"game_media/{game_id}/{folder}/{os.path.basename(name)}"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            print("converting cover img to png")
            f.write(convert_to_png(requests.get(source)).getvalue())
            return

    if media_type not in ['image', 'video']:
        raise ValueError("Invalid media type")

    r = requests.get(source)
    if r.headers.get('Content-Length'):
        if int(r.headers['Content-Length']) < 1024 * 40:
            print("File too small, skipping.")
            return

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    print(f"Downloading {media_type} from {source}")
    with open(save_path, 'wb') as f:
        f.write(r.content)

def download_page_media(driver: WebDriver, kettle_game_id: int):

    total_images = 0
    total_videos = 0

    try:
        cover_image = driver.find_element(By.CLASS_NAME, "game_header_image_full").get_attribute("src")
        images = driver.find_elements(By.CLASS_NAME, "highlight_screenshot_link")
        video = driver.find_element(By.CSS_SELECTOR, "video[id^='movie_']")
    except Exception as e:
        print("Error finding media on page:", e)
        return

    img_urls = [img.get_attribute("href").split("?")[0] for img in images if '/store_item_assets/' in img.get_attribute("href")]
    video_src = video.get_attribute("src").split("?")[0] if video else None

    download_file(cover_image, kettle_game_id, media_type='image', name="cover")

    for img in img_urls:
        if total_images > 5:
            break
        download_file(img, kettle_game_id, "image")
        total_images += 1


    if video_src:
        download_file(video_src, kettle_game_id, "video")

# Metadata extraction
def get_game_metadata(driver: WebDriver):
    blacklisted_strings = [
        "ABOUT THIS GAME"
    ]

    data = {
        'title': driver.find_element(By.ID, "appHubAppName").text,
        'description': driver.find_element(By.ID, "game_area_description").text,
        'tags': set(tag.text for tag in driver.find_elements(By.CLASS_NAME, "app_tag")),
        'release_date': driver.find_element(By.CLASS_NAME, "date").text
    }

    for s in blacklisted_strings:
        if s in data['description']:
            data['description'] = data['description'].replace(s, "")

    for item in blacklisted_tags:
        if item in data['tags']:
            raise "Blacklisted tag found on game."
    return data

# Genre loading/creation
def load_kettle_genres():
    global master_tag_set
    with app.app_context():
        master_tag_set = set(x.genre_tag for x in db.session.query(Genre).all())

def create_kettle_genre(tag):
    with app.app_context():
        new_tag = Genre(genre_tag=tag)
        db.session.add(new_tag)
        db.session.commit()
        master_tag_set.add(tag)


def convert_to_png(r: requests.Response):
    if r.status_code == 200:
        img = Image.open(BytesIO(r.content))  # Open image from bytes
        buffer = BytesIO()
        img.convert("RGBA").save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

# Game creation
def create_kettle_game(title, description, dt_string, genres) -> int:
    global games_added
    genre_ignores = ["+", ""]
    game_prices = [1000, 2000, 3000, 4000, 5000]


    with app.app_context():
        check_db_for_game = db.session.query(Game).filter_by(game_title=title).first()
        if check_db_for_game:
            raise "Game already exists"
        game = Game(
            game_title=title,
            game_price=random.choice(game_prices),
            game_desc=description,
            game_releasedate=datetime.strptime(dt_string, "%b %d, %Y").date()
        )
        db.session.add(game)
        db.session.commit()

        for genre in genres:
            genre = genre.lower()
            if genre not in master_tag_set and genre not in genre_ignores:
                try:
                    create_kettle_genre(genre)
                except Exception as e:
                    print("Failed to create genre:", genre, e)

        for genre in genres:
            genre = genre.lower()
            if genre not in genre_ignores:
                try:
                    genre_obj = db.session.query(Genre).filter_by(genre_tag=genre).first()
                    if genre_obj:
                        db.session.add(GameGenre(game_id=game.game_id, genre_id=genre_obj.genre_id))
                        db.session.commit()
                except Exception as e:
                    print("Failed to link genre:", genre, e)

        games_added += 1
        return game.game_id

# Game link extraction
def find_game_pages(driver: WebDriver):
    global game_page_set
    if len(game_page_set) >= config['crawler']['limit']:
        return []

    a_tags = driver.find_elements(By.TAG_NAME, 'a')
    pattern = r'https://store\.steampowered\.com/app/\d+/[A-Za-z0-9_]+(?:\?snr=\d+_\d+_\d+__\d+)?'
    links = [x.get_attribute("href") for x in a_tags if x.get_attribute("href") and re.match(pattern, x.get_attribute("href")) and "/Steam_Deck/" not in x.get_attribute("href")]
    game_page_set.update(links)
    return links

# Main driver
load_kettle_genres()
print(f"Loaded kettle genres: {master_tag_set}")
driver = startup_marionette()
driver.get(config['crawler']['target_url'])

# Initial crawl
for item in find_game_pages(driver):
    if games_added >= config['crawler']['limit']:
        break
    try:
        driver.get(item)
        metadata = get_game_metadata(driver)
        game_id = create_kettle_game(metadata['title'], metadata['description'], metadata['release_date'], metadata['tags'])
        download_page_media(driver, game_id)
        find_game_pages(driver)
    except Exception as e:
        print(f"Failed to process {item}: {e}")

print(f"Total games added: {games_added}")
