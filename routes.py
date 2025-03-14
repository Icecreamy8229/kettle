import datetime
import os
import re
import yaml
from flask import render_template, Blueprint, request, redirect, url_for, flash, jsonify, send_from_directory
import logging
import random
from models import db, User, Cart, Game, Library
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from login import load_user
from email_utils import send_verify_email, verify_token

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
routes = Blueprint('routes', __name__)  # this module points to itself for routes.
trusted_users = "kero rubber gene savbun squarebrian".split()

@routes.route('/')  # This is the general syntax for creating a route in flask.
def index_route():
    games = db.session.query(Game).filter_by(game_active=True).order_by(Game.game_releasedate.desc()).limit(10).all()
    random.shuffle(games)
    logging.debug('Index route called')
    return render_template('index.html',games=games)

@routes.route('/checkout')
def checkout_route():
    logging.debug('Checkout route called')
    return render_template('checkout.html', title='Checkout')

@routes.route('/about')
def about_route():
    logging.debug('About route called')
    return render_template('about.html', title='About')


@login_required
@routes.route('/user')
def user_route():
    logging.debug('User route called')
    if current_user.is_authenticated:
        return render_template('user.html')
    else:
        return render_template('login.html', title='Login')

@login_required
@routes.route('/library')
def library_route():
    logging.debug('Library route called')
    if not current_user.is_authenticated:

        return render_template('login.html')
        
    library_items = db.session.query(Library).filter_by(user_id=current_user.user_id).all()
    game_ids = [i.game_id for i in library_items]
    games = db.session.query(Game).filter(Game.game_id.in_(game_ids)).all()
    logging.info(f"Library route called, with these items: {games}")
    return render_template("library.html", games=games)

@routes.route('/testing')
def testing_route():
    return render_template('index.html')  # used for testing purposes.  when I need to test certain things I throw it under this route.


@routes.route("/settings")
@login_required
def settings_route(): #not used yet.
    return url_for('routes.index_route')


@routes.route("/game")
def game_route():

    game_id = request.args.get("id", type=int)

    if not game_id:
        logging.info("Game ID not provided in query parameters.")
        return "404 Not Found"

    game = db.session.query(Game).filter_by(game_id=game_id).first()
    if not game:
        logging.info(f"Game with ID {game_id} not found.")
        return "404 Not Found"

    logging.info(f"Game route called for game: {game}")
    MEDIA_DIR = 'game_media'
    game_path = os.path.join(MEDIA_DIR, str(game_id))
    image_path = os.path.join(game_path, "images")
    video_path = os.path.join(game_path, "videos")
    media_files = []

    def add_media_from_directory(directory, media_type):
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                file_url = f"/game_media/{game_id}/{media_type}/{filename}"
                if media_type == "images" and filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                    media_files.append({"type": "image", "url": file_url})
                elif media_type == "videos" and filename.lower().endswith((".mp4", ".webm", ".ogg")):
                    media_files.append({"type": "video", "url": file_url})

    add_media_from_directory(image_path, "images")
    add_media_from_directory(video_path, "videos")


    return render_template(
        'game.html',
        game=game,
        user=current_user,
        title=game.game_title,
        media_files=media_files
    )


@routes.route("/login", methods=['GET', 'POST'])
def login_route():
    if current_user.is_authenticated:  # no need for an authenticated logged in user to get to this page.
        return redirect(url_for('routes.index_route'))

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        user = db.session.query(User).filter_by(user_login=username).first()
        if user and user.verify_password(password):
            logging.info(f"{user.user_login} has successfully logged in")
            login_user(user)
            flash(f'You are now logged in as {user.user_login}', "success")
            return redirect(url_for('routes.index_route'))

        else:
            logging.info(f"Invalid username or password, attempted login: {username}")
            flash("Invalid username or password", "danger")

    return render_template('login.html', title='Login')


@routes.route("/signup", methods=['POST'])
def signup_route(): #this is only used to process data from the form and sign the user up.
    def has_special_characters(s):
        return bool(re.search(r'[^a-zA-Z0-9]', s))

    def verify_email(email):
        return bool(re.search(r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', email))

    def verify_password(password):
        if len(password) < 8:
            return False
        if not any(char.isupper() for char in password):
            return False
        if not has_special_characters(password):
            return False

        return True

    #the logic is not done yet.
    #use helper.py to create users for dev environment
    if current_user.is_authenticated:
        return redirect(url_for('routes.index_route'))

    data = request.form
    alias = data.get('alias')
    user_login = data.get('username')
    password = data.get('password')
    confirm_password = data.get('password-confirm')
    email = data.get('email')
    if not user_login or not email or not password:
        logging.info(f"Missing required fields: {user_login}, {email}, {password}")
        return jsonify({'error': 'Missing required fields'}), 400

    if password != confirm_password:
        logging.info(f"Passwords do not match for {user_login}")
        return jsonify({'error': 'Passwords do not match'}), 400

    if not verify_password(password):
        logging.info(f"Password for {user_login} is not strong enough.")
        return jsonify({'error': 'Password is not strong enough'}), 400

    existing_user = db.session.query(User).filter_by(user_login=user_login).first()
    existing_email = db.session.query(User).filter_by(user_email=email).first()
    if existing_user or existing_email:
        logging.info(f"User already exists for login: {user_login} or email: {email}")
        return jsonify({'error': 'User already exists'}), 400

    if has_special_characters(user_login) or not verify_email(email):
        logging.info(f"Invalid username or email for {user_login}")
        return jsonify({'error': 'Invalid username or email'}), 400

    new_user = User()
    new_user.user_login = user_login
    new_user.user_email = email
    new_user.user_alias = alias
    new_user.password = password
    if config['environment'] != 'production':
        logging.info(f"User {user_login} created in dev env, verification bypassed.")
        new_user.user_verified = True
    db.session.add(new_user)
    db.session.commit()
    if config['environment'] == 'production':
        send_verify_email(new_user)

    login_user(new_user)
    flash("Please check your email for a verification link.", "success")
    return redirect(url_for('routes.index_route'))







@login_required
@routes.route("/cart")
def cart_route():
    if not current_user.is_authenticated:
        logging.info(f"Cart route called, but the user is not authenticated.")
        return redirect(url_for('routes.index_route'))

    cart_items = db.session.query(Cart).filter_by(user_id=current_user.user_id).all()
    game_ids = [i.game_id for i in cart_items]
    games = db.session.query(Game).filter(Game.game_id.in_(game_ids)).all()
    logging.info(f"Cart route called, with these items: {games}")
    return render_template("cart.html", games=games)


@routes.route("/logout")
@login_required
def logout_route():
    logout_user()
    flash("You have been logged out", "success")
    return redirect(url_for('routes.index_route'))

@login_required
@routes.route("/submission")
def submission_route(): #trusted users can create games here.
    global trusted_users

    if current_user.is_authenticated and current_user.user_login in trusted_users:
        return render_template('submission.html')

    return redirect(url_for('routes.index_route'))


@routes.route("/submit-game", methods=['POST'])
def submit_game_route():
    global trusted_users

    if current_user.is_authenticated and current_user.user_login not in trusted_users:
        return jsonify({'error': 'User not allowed.'}), 400
    if 'game-images' not in request.files or 'game-videos' not in request.files:
        return jsonify({'error': 'Files are missing'}), 400

    game_title = request.form.get('game-title', '').strip()
    if not game_title:
        return jsonify({'error': 'Game title is required'}), 400

    image_files = request.files.getlist('game-images')
    video_files = request.files.getlist('game-videos')
    print(len(video_files))
    print(len(image_files))

    max_files = 10
    max_image_size = 4 * 1024 * 1024  # 4MB in bytes
    max_video_size = 25 * 1024 * 1024  # 25MB in bytes

    if len(image_files) + len(video_files) > max_files:
        return jsonify({'error': 'A maximum of 10 files (images and videos) is allowed'}), 400

    if len(video_files) > 1:
        return jsonify({'error': 'Only one video file is allowed'}), 400

    for file in image_files:
        print(f"image file: {file.filename}")
        if file.content_type.split('/')[0] != 'image':
            return jsonify(
                {'error': f"Only image files are allowed in the image upload (problem with {file.filename})"}), 400
        if file.content_length > max_image_size:
            return jsonify({'error': 'Each image must be smaller than 4MB'}), 400

    for file in video_files:
        # Check if the file is empty or not
        if file.filename and file.content_type.split('/')[0] != 'video':
            return jsonify(
                {'error': f"Only video files are allowed in the video upload (problem with {file.filename})"}), 400
        if file.content_length > max_video_size:
            return jsonify({'error': 'Each video must be smaller than 25MB'}), 400

    # Check if the game already exists (case-insensitive check)
    game = Game.query.filter(Game.game_title.ilike(game_title)).first()
    if game:
        return jsonify({'error': 'Game already exists'}), 400

    game = Game()
    game.game_title = game_title
    game.game_desc = request.form.get('game-desc', '')

    try:
        game.game_price = int(request.form.get('game-price', 0))
    except ValueError:
        return jsonify({'error': 'Game price must be a valid number'}), 400

    game.game_releasedate = datetime.date.today()
    db.session.add(game)
    db.session.commit()

    MEDIA_DIR = 'game_media'
    game_dir = os.path.join(MEDIA_DIR, str(game.game_id))
    images_dir = os.path.join(game_dir, 'images')
    videos_dir = os.path.join(game_dir, 'videos')

    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(videos_dir, exist_ok=True)

    # Save files
    for index, file in enumerate(image_files):
        filename = 'cover.png' if index == 0 else file.filename
        # Check if a cover image already exists
        if filename == 'cover.png' and os.path.exists(os.path.join(images_dir, filename)):
            return jsonify({'error': 'Cover image already exists, please upload a different one'}), 400
        file.save(os.path.join(images_dir, filename))

    for file in video_files:
        # If there's a file to save, do it
        if file.filename:
            file.save(os.path.join(videos_dir, file.filename))
    flash(f"{game_title} has submitted successfully!", "success")
    return redirect(url_for('routes.index_route'))


@routes.route("/verify-email/<token>")
def verify_email(token):

    email = verify_token(token)
    if not email:
        return redirect(url_for("routes.index_route"))

    user = User.query.filter_by(user_email=email).first()
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("routes.index_route"))

    user.user_verified = True  # Mark user as verified
    db.session.commit()

    flash("Your email has been verified!", "success")
    return redirect(url_for("routes.index_route"))

@routes.route('/game_media/<int:game_id>/<path:filename>')
def serve_game_media(game_id, filename):
    return send_from_directory(f'game_media/{game_id}/', filename)
#TODO I dont think I ended up needing this route, probably can be deleted.