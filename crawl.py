import os
import random
import requests
from bs4 import BeautifulSoup
from models import Game, db
import re
from main import app
from datetime import datetime
from PIL import Image
from io import BytesIO

#TODO prevent NSFW games from appearing.
#TODO move over to Selenium to let javascript render bigger images.



GAME_LIMIT = 25 #number of games you want to download data for.
games_added = 0

game_page_list = set()

def crawl(url):
    """
    Gets the soup for a page.
    :param url:
    :return: BeautifulSoup object.
    """
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup


def find_game_pages(page_soup: BeautifulSoup):
    """
    Updates the set of game pages.
    :param page_soup:
    :return: None
    """
    global game_page_list
    print(len(game_page_list))
    if len(game_page_list) >= GAME_LIMIT:
        return

    links = [x.get("href") for x in page_soup.find_all('a') if x.get('href')]
    pattern = r'https://store\.steampowered\.com/app/\d+/[A-Za-z0-9_]+(?:\?snr=\d+_\d+_\d+__\d+)?'
    links = [x for x in links if re.match(pattern, x) and x.find("/Steam_Deck/") == -1]
    game_page_list.update(links)
    return links

def create_kettle_game(page_soup: BeautifulSoup):
    global games_added
    game_prices = [1000, 2000, 3000, 4000, 5000]


    with app.app_context():
        game = Game()
        game.game_title = page_soup.find('div', class_='apphub_AppName').text
        game.game_price = random.choice(game_prices)
        short_desc = page_soup.find('div', class_='game_description_snippet').text #use later.
        game.game_desc = page_soup.find('div', class_='game_area_description').text
        game.game_releasedate = datetime.strptime(page_soup.find('div', class_='date').text, "%b %d, %Y").date()
        db.session.add(game)
        db.session.commit()
        download_images(page_soup, game.game_id)
        print(f"Added game {game.game_title} {game.game_id}")

    games_added += 1


def convert_to_png(r: requests.Response):
    if r.status_code == 200:
        img = Image.open(BytesIO(r.content))  # Open image from bytes
        buffer = BytesIO()
        img.convert("RGBA").save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

def download_images(page_soup: BeautifulSoup, kettle_game_id: int):
    img_urls = []
    cover_image = page_soup.find('img', class_='game_header_image_full')
    cover_img_source = cover_image['src'].split("?")[0]
    image_container = page_soup.select(".highlight_overflow img")
    try:
        for img in image_container:
            src = img['src']
            if '/store_item_assets/' in src:
                img_urls.append(src.split("?")[0])

    except Exception as e:
        return

    for img in img_urls:


        print(img)
        r = requests.get(img)
        if r.headers.get('Content-Length'):
            content_length = int(r.headers.get('Content-Length'))
            if content_length < 1024 * 40:
                print("too small, skipping")
                continue
        else:
            continue

        image_path = f"game_media/{kettle_game_id}/images/{img.split('/')[-1]}"
        if "cover" in img:
            print(f"skipping {img} because it has cover in the name.")
            continue
        os.makedirs(os.path.dirname(image_path),exist_ok=True)




        with open(image_path, 'wb') as f:
            f.write(r.content)


    cover_image_path = f"game_media/{kettle_game_id}/images/cover.png"
    os.makedirs(os.path.dirname(cover_image_path), exist_ok=True)
    with open(cover_image_path, 'wb') as f:

        print("converting cover img to png")
        f.write(convert_to_png(requests.get(cover_img_source)).getvalue())








def main():
    steam_crawl = crawl("https://store.steampowered.com")
    for item in find_game_pages(steam_crawl):
        if len(game_page_list) >= GAME_LIMIT:
            break
        find_game_pages(crawl(item))

    for item in game_page_list:
        if games_added >= GAME_LIMIT:
            break
        try:

            create_kettle_game(crawl(item))

        except Exception as e:
            print(e)
            continue



if __name__ == "__main__":
    main()
