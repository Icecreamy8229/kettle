from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import ForeignKey, DateTime
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)


class Cart(db.Model): #linking table
    __tablename__ = 'carts'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'), primary_key=True, nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey('games.game_id'), primary_key=True, nullable=False)


class Library(db.Model): #linking table
    __tablename__ = 'libraries'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'), primary_key=True, nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey('games.game_id'), primary_key=True, nullable=False)


class ProfilePicture(db.Model):
    __tablename__ = 'profile_pictures'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'), primary_key=True, nullable=False)
    profile_pic_path: Mapped[str] = mapped_column(nullable=True) #TODO change this to a default picture path remove null


class User(db.Model):
    __tablename__ = 'users'
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    user_alias: Mapped[str] = mapped_column(nullable=False)
    user_email: Mapped[str] = mapped_column(nullable=False, unique=True)
    user_login: Mapped[str] = mapped_column(nullable=False, unique=True)
    user_password: Mapped[str] = mapped_column(nullable=False)
    user_balance: Mapped[int] = mapped_column(default=10_000, nullable=False)
    user_createdt: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), nullable=False)
    @property
    def password(self) -> str:
        raise AttributeError("Password is write-only!")

    @password.setter #when password is set, it is modified to be hashed.
    def password(self, plain_password: str) -> str:
        self.user_password = bcrypt.generate_password_hash(plain_password).decode('utf-8')

    def verify_password(self, plain_password: str) -> bool: #compares the two hashes from attempted pass with stored pass
        return bcrypt.check_password_hash(self.user_password, plain_password)


class Game(db.Model):
    __tablename__ = 'games'
    game_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    game_title: Mapped[str] = mapped_column(nullable=False)
    game_price: Mapped[int] = mapped_column(nullable=False)
    game_desc: Mapped[str] = mapped_column(nullable=False)
    game_sale: Mapped[float] = mapped_column(nullable=False, default=0.00)
    game_releasedate: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    game_active: Mapped[bool] = mapped_column(default=True, nullable=False)

class Genre(db.Model):
    __tablename__ = 'genres'
    genre_id: Mapped[int] = mapped_column(primary_key=True, nullable=False, autoincrement=True, unique=True)
    genre_name: Mapped[str] = mapped_column(nullable=False, unique=True)

class GameGenre(db.Model): #linking table
    __tablename__ = 'game_genres'
    genre_id: Mapped[int] = mapped_column(ForeignKey('genres.genre_id'), nullable=False, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey('games.game_id'), nullable=False, primary_key=True)


class Order(db.Model):
    __tablename__ = 'orders'
    order_id: Mapped[int] = mapped_column(nullable=False, primary_key=True, autoincrement=True, unique=True)
    order_userid: Mapped[int] = mapped_column(nullable=False)
    order_gid: Mapped[int] = mapped_column(nullable=False)
    order_gtitle: Mapped[str] = mapped_column(nullable=False)
    order_price: Mapped[int] = mapped_column(nullable=False)
    order_dt: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), nullable=False)


if __name__ == '__main__': #if you run models.py independently, it can create new tables based on the defined models.

    from flask import Flask
    import yaml
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    app = Flask(__name__, template_folder='templates')
    app.config[
        "SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{config['database']['username']}:{config['database']['password']}@{config['database']['host']}/{config['database']['schema']}"

    db.init_app(app)
    with app.app_context():
        db.create_all()