import datetime
import os
import re
import yaml
from flask import render_template, Blueprint, request, redirect, url_for, flash, jsonify, send_from_directory
import logging
import random

from flask_wtf.csrf import CSRFError
from requests import session

from models import db, User, Cart, Game, Library
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from login import load_user
from email_utils import send_verify_email, verify_token
from sqlalchemy.exc import SQLAlchemyError



# User media limitations
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 1_048_576  # 1MB

bcyrpt = Bcrypt()

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
routes = Blueprint('routes', __name__)  # this module points to itself for routes.


@routes.route('/')  # This is the general syntax for creating a route in flask.
def index_route():
    games = db.session.query(Game).filter_by(game_active=True).order_by(Game.game_releasedate.desc()).limit(10).all()
    random.shuffle(games)
    logging.debug('Index route called')
    return render_template('index.html',games=games)

@login_required
@routes.route('/checkout', methods=['GET', 'POST',])
def checkout_route():
    exists_in_library = db.session.query(
        db.session.query(Library).filter(
            Library.user_id == current_user.user_id,
            Library.game_id == Cart.game_id
        ).exists()
    ).filter(Cart.user_id == current_user.user_id).all()

    if True in exists_in_library:
        flash(f"error: some games already owned.", "danger")
        return redirect(url_for('routes.cart_route'))
    users_cart = db.session.query(Cart).filter_by(user_id=current_user.user_id).all()

    game_ids = [cart_item.game_id for cart_item in users_cart]
    games = db.session.query(Game).filter(Game.game_id.in_(game_ids)).all()
    total_price = sum([x.game_price for x in games])
    if total_price == 0:
        return redirect(url_for('routes.index_route'))
    if total_price > current_user.user_balance:
        flash("You don't have enough points to complete the purchase.", "danger")
        return redirect(url_for('routes.cart_route'))

    current_user.user_balance -= total_price
    db.session.flush()
    for cart_item in users_cart:
        db.session.add(Library(user_id=current_user.user_id, game_id=cart_item.game_id))
        db.session.delete(cart_item)
    db.session.commit()

    return render_template('checkout.html', title='Checkout', purchases=games, total_price=total_price)

@routes.route('/about')
def about_route():
    logging.debug('About route called')
    return render_template('about.html', title='About')


@routes.route('/user')
@login_required
def user_route():
    logging.debug('User route called')
    if current_user.is_authenticated:
        return render_template('user.html')
    else:
        return render_template('login.html', title='Login')
    
# Add game points to user balance
@routes.route('/add-game-points', methods=['POST'])
@login_required
def add_game_points():
    try:
        points = request.form.get('game-points')
        if not points or not points.isdigit() or int(points) != 5000:
            return jsonify({"error": "Invalid points value"}), 400

        user = User.query.get(current_user.user_id)
        user.user_balance += int(points)
        db.session.commit()
        return jsonify({"success": True, "points": points}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



@routes.route('/search-results', methods=['GET'])
def search_results_route():
    def create_json(game: Game):
        return {
            "game_id": game.game_id,
            "game_title": game.game_title,
            "game_desc": game.game_desc,
            "game_price": game.game_price,
        }

    search_param = request.args.get('search', type=str)
    try:
        # Query the games table for titles that match the search term (case-insensitive)
        games = Game.query.filter(Game.game_title.ilike(f"%{search_param}%")).all()
        #games = db.query(Game).filter(Game.game_title.ilike(search_param)).all() savannahs code
        print(games)
    except Exception as e:
        logging.error(f"Error while querying the database: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

    if not games:
        return jsonify([])  # If no games are found, return an empty list

    # If games are found, convert them to JSON
    results = [create_json(game) for game in games]
    return jsonify(results)


@routes.route('/update_user', methods=['POST'])
@login_required
def update_user_route():
    logging.debug('Update user route called')

    # Get form data
    alias = request.form.get('alias')
    bio = request.form.get('bio')
    profile_picture = request.files.get('profile_picture')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # Update user alias and bio if provided
    if alias:
        current_user.user_alias = alias
    if bio:
        current_user.user_bio = bio

    # Profile Picture Upload Handling
    if profile_picture:
        filename = secure_filename(profile_picture.filename)
        if '.' in filename:
            file_ext = filename.rsplit('.', 1)[1].lower()

            if file_ext not in ALLOWED_EXTENSIONS:
                flash('Invalid file type. Only PNG, JPG, and JPEG are allowed.', 'danger')
                return redirect(url_for('routes.user_route'))

            if profile_picture.content_length > MAX_FILE_SIZE:
                flash('Profile picture size should be less than 1MB.', 'danger')
                return redirect(url_for('routes.user_route'))

            # Save profile picture with a user-specific filename
            profile_picture_filename = f"profile_picture.{file_ext}"
            profile_picture_path = os.path.join(f'user_profiles/{current_user.user_id}', profile_picture_filename)
            folder = os.path.dirname(profile_picture_path)
            os.makedirs(folder, exist_ok=True)
            profile_picture.save(profile_picture_path)
            current_user.user_picture = profile_picture_filename

    if request.is_json and request.json.get('password'):
        validate = current_user.verify_password(request.json.get('password'))
        if validate:
            return jsonify({'valid': True})
        else:
            return jsonify({'valid': False})


    # Password Update Handling
    if new_password:
        if not current_user.verify_password(current_password):
            flash('Incorrect current password.', 'danger')
            return redirect(url_for('routes.user_route'))

        if new_password != confirm_password:
            flash('New password and confirmation do not match.', 'danger')
            return redirect(url_for('routes.user_route'))

        # Update password

        current_user.password = confirm_password
        flash('Your password has been updated.', 'success')

    # Save all changes to database
    try:
        db.session.commit()
        flash('Your profile has been updated.', 'success')
    except Exception as e:
        db.session.rollback()
        flash("An error occurred. Please try again.", "danger")
        logging.error(f"Error updating user: {e}")

    return redirect(url_for('routes.user_route'))
    

        
    

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

    def verify_email(email: str) -> bool:
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        return bool(re.match(pattern, email))

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
    email = data.get('email').strip().lower()
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

    if has_special_characters(user_login):
        logging.info(f"User {user_login} has special characters.")
        return jsonify({'error': 'Invalid username'}), 400

    if not verify_email(email):
        logging.info(f"Invalid email for {user_login} with email: {email}")
        return jsonify({'error': 'Invalid email'}), 400

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
    return render_template("cart.html", games=games, total_price=sum([i.game_price for i in games]))


@routes.route("/logout")
@login_required
def logout_route():
    logout_user()
    flash("You have been logged out", "success")
    return redirect(url_for('routes.index_route'))

@login_required
@routes.route("/submission")
def submission_route(): #trusted users can create games here.


    if current_user.is_authenticated and current_user.user_privilege > 0:
        return render_template('submission.html')

    return redirect(url_for('routes.index_route'))


@routes.route("/submit-game", methods=['POST'])
def submit_game_route():


    if current_user.is_authenticated and current_user.user_privilege < 1:
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
    max_video_size = 35 * 1024 * 1024  # 35MB in bytes

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
            return jsonify({'error': 'Each video must be smaller than 35MB'}), 400

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

#ALL AI GENERATED, JUST SO I CAN SEE IF THE CART PAGE WORKS.
@routes.route("/add-to-cart", methods=['POST'])
@login_required
def add_to_cart_route():
    data = request.form
    game_id = data.get("game_id")

    if not game_id:
        return jsonify({'error': 'Game ID is required'}), 400

    game = db.session.query(Game).filter_by(game_id=game_id).first()
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    # Check if game is already in cart
    existing_cart_item = db.session.query(Cart).filter_by(user_id=current_user.user_id, game_id=game_id).first()
    if existing_cart_item:
        flash(f"{game.game_title} is already in your cart", "warning")
        return redirect(url_for('routes.index_route'))

    check_in_library = db.session.query(Library).filter_by(user_id=current_user.user_id, game_id=game_id).first()
    if check_in_library:
        flash(f"{game.game_title} is already in your library", "warning")
        return redirect(url_for('routes.index_route'))
    cart_item = Cart(user_id=current_user.user_id, game_id=game_id)
    db.session.add(cart_item)
    db.session.commit()

    flash(f"{game.game_title} added to cart", "success")
    return redirect(url_for('routes.index_route'))


#ALL AI GENERATED, JUST SO I CAN SEE IF THE CART PAGE WORKS.
@routes.route("/remove-from-cart", methods=['POST'])
@login_required
def remove_from_cart():
    data = request.get_json()
    game_id = data.get("game_id")

    if not game_id:
        return jsonify({'error': 'Game ID is required'}), 400

    cart_item = db.session.query(Cart).filter_by(user_id=current_user.user_id, game_id=game_id).first()
    
    if not cart_item:
        return jsonify({'error': 'Game not found in cart'}), 404

    db.session.delete(cart_item)
    db.session.commit()

    return jsonify({'success': True}), 200


@routes.route('/profile_pictures/<path:filename>')
def profile_pictures(filename):
    return send_from_directory('user_profiles', filename)

@routes.errorhandler(CSRFError)
def handle_csrf_error(e):
    return str(e.description), 400
