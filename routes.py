import datetime
import os
import re
from math import ceil

import yaml
from flask import render_template, Blueprint, request, redirect, url_for, flash, jsonify, send_from_directory, session
import logging
import random

from flask_wtf.csrf import CSRFError

from models import db, User, Cart, Game, Library, Flappybird, GameGenre, Genre, Order
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

from email_utils import send_verify_email, verify_token

from helper import get_game_media




# User media limitations
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 1_048_576  # 1MB

bcyrpt = Bcrypt()

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
routes = Blueprint('routes', __name__)  # this module points to itself for routes.

game_media = os.listdir("./game_media/")
games_on_display = [directory for directory in game_media if len(os.listdir(f"./game_media/{directory}/videos")) > 0]
@routes.route('/')  # This is the general syntax for creating a route in flask.
def index_route():

    current_time = datetime.datetime.now().timestamp()
    def load_videos_from_session(game_list: [int]):
        games = Game.query.filter(Game.game_id.in_(game_list)).all()
        for game in games:
            game.video_path = get_game_media("videos", game)[0]['url']
        return games

    def load_index_videos():



        selected_game_ids = random.sample(games_on_display, 3)
        #this makes sure only games that actually have a video are loaded, rather than a game with no video causing an error.
        games_selected = db.session.query(Game).filter(Game.game_id.in_(selected_game_ids)).all()

        for game in games_selected:
            game.video_path = get_game_media("videos", game)[0]['url']

        return games_selected

    if not session.get('banner-last-set'):
        logging.info("Banner never set, setting...")
        session['banner-last-set'] = current_time

        index_banner_games = load_index_videos()
        session['index-banner-games'] = [x.game_id for x in index_banner_games]

    elif current_time - session.get('banner-last-set') > (60 * 60): #limited to an hour
        logging.info(f"time delta is greater than 60 minutes, setting new banner...")
        session['banner-last-set'] = current_time
        index_banner_games = load_index_videos()
        session['index-banner-games'] = [x.game_id for x in index_banner_games]

    else:
        logging.info(f"Banner games loaded from session: {session.get('banner-last-set')}")
        index_banner_games = load_videos_from_session(session['index-banner-games'])



    page = request.args.get('page', 1, type=int)
    all_games = db.session.query(Game).filter_by(game_active=True).order_by(Game.game_releasedate.desc()).all()
    per_page = 15
    total_pages = ceil(len(all_games) / per_page)
    total_games = len(all_games)


    logging.debug('Index route called')
    start = (page - 1) * per_page
    end = start + per_page
    games = all_games[start:end]
    return render_template('index.html',games=games,
                           page=page,
                           total_pages=total_pages,
                           total_games=total_games,
                           index_banner_games=index_banner_games)

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

    for cart_item in users_cart:


        db.session.add(Library(user_id=current_user.user_id, game_id=cart_item.game_id))

        db.session.delete(cart_item)
    db.session.flush()

    for game in games:
        order = Order(order_userid=current_user.user_id, order_gid=game.game_id, order_gtitle=game.game_title,
                      order_price=game.game_price)
        db.session.add(order)

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
    from helper import get_game_media


    game_id = request.args.get("id", type=int)

    if not game_id:
        logging.info("Game ID not provided in query parameters.")
        return "404 Not Found"

    game = db.session.query(Game).filter_by(game_id=game_id).first()
    genres = (
        db.session.query(Genre.genre_tag)
        .join(GameGenre, Genre.genre_id == GameGenre.genre_id)
        .filter(GameGenre.game_id == game_id)
        .all()
    )


    if not game:
        logging.info(f"Game with ID {game_id} not found.")
        return "404 Not Found"

    logging.info(f"Game route called for game: {game}")



    media_files = []
    media_files.extend(get_game_media("videos", game))
    media_files.extend(get_game_media("images", game))



    return render_template(
        'game.html',
        game=game,
        user=current_user,
        title=game.game_title,
        media_files=media_files,
        genres=genres,
    )


@routes.route("/login", methods=['GET', 'POST'])
def login_route():
    if current_user.is_authenticated:  # no need for an authenticated logged in user to get to this page.
        return redirect(url_for('routes.index_route'))

    if request.method == "POST":
        username_or_email = request.form['username']
        password = request.form['password']

        is_email = re.match(r"[^@]+@[^@]+\.[^@]+", username_or_email)

        if is_email:

            user = db.session.query(User).filter_by(user_email=username_or_email).first()
        else:

            user = db.session.query(User).filter_by(user_login=username_or_email).first()

        if user and user.verify_password(password):
            logging.info(f"{user.user_login} has successfully logged in")
            login_user(user)
            flash(f'You are now logged in as {user.user_login}', "success")
            return redirect(url_for('routes.index_route'))

        else:
            logging.info(f"Invalid username or password, attempted login: {username_or_email}")
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


@routes.route("/remove-from-cart", methods=['POST'])
@login_required
def remove_from_cart_route():
    data = request.form
    game_id = data.get("game_id")
    if not game_id:
        return jsonify({'error': 'Game ID is required'}), 400
    cart_item = db.session.query(Cart).filter_by(user_id=current_user.user_id, game_id=game_id).first()
    if not cart_item:
        return jsonify({'error': 'Game not found in cart'}), 404
    db.session.delete(cart_item)
    db.session.commit()
    flash("Item removed from cart", "success")
    return redirect(url_for('routes.cart_route'))


@routes.route("/kettle-bird")
@login_required
def kettle_bird_route():
    #TODO will want to hide behind a "paywall" eventually.

    session['flappybird_ts'] = datetime.datetime.now().timestamp()
    game_owned = db.session.query(Library).filter_by(user_id=current_user.user_id, game_id=276).first()
    if not game_owned:
        flash("Please purchase the game.", "danger")
        return redirect(url_for('routes.game_route') + "?id=276")

    highscores = (
        db.session.query(User.user_alias, Flappybird.flappybird_highscore)
        .join(Flappybird, Flappybird.user_id == User.user_id)
        .order_by(Flappybird.flappybird_highscore.desc())
        .limit(10)
        .all()
    )

    return render_template('games/kettle_bird.html',highscores=highscores)

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


@routes.route('/submit-score', methods=['POST'])
def submit_score_route():
    game_start_time = session.get('flappybird_ts')
    game_finish_time = datetime.datetime.now().timestamp()
    multiplier = 1.35
    delta = game_finish_time - game_start_time

    if not current_user.is_authenticated:
        return jsonify({'error': 'user is not logged in'}), 401

    data = request.get_json()
    score = data.get('score')
    if not score:
        return jsonify({'error': 'Score is required'}), 400

    def verify_score(score: int):
        return (float(delta) * multiplier) > float(score)



    def reset_game_start_time():
        session['flappybird_ts'] = datetime.datetime.now().timestamp()

    if not verify_score(score):
        logging.info(
            f"CHEATER user {current_user.user_login} score is {score} with a time delta of {delta * multiplier}")
        return jsonify({'error': 'Cheater'}), 400

    reset_game_start_time()
    highscore = db.session.query(Flappybird).filter_by(user_id=current_user.user_id).first()

    if not highscore:
        highscore = Flappybird(user_id=current_user.user_id, flappybird_highscore=score)
        db.session.add(highscore)
        db.session.commit()

    if not isinstance(score, int) or score < 0 or score > 999999: # cheaters >:(
        highscore.flappybird_cheater = True
        db.session.add(highscore)
        db.session.commit()
        return jsonify({'success': False, 'error': 'Invalid score'}), 400


    elif highscore.flappybird_cheater:
        return jsonify({'success': False, 'error': 'cheater'}), 400


    if score > highscore.flappybird_highscore:
        logging.info(f"Flappybird score update for User: {current_user.user_login}, Score: {score}")
        highscore.flappybird_highscore = score
        db.session.add(highscore)
        db.session.commit()
    return jsonify({'success': True}), 200


@routes.route('/slider-games')
def slider_games():

    import os
    game_images_dir = 'static/images/games/'

    media_files = [os.path.join(game_images_dir, f) for f in os.listdir(game_images_dir) if
                   f.endswith(('.jpg', '.png', '.gif'))]

    return render_template('index.html', media_files=media_files)
