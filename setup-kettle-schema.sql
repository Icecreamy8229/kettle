/* 
Careful, this script blows away the database and recreates it
author: ggw 2/26/2025
*/

DROP DATABASE IF EXISTS kettle;
CREATE DATABASE kettle;
USE kettle;

CREATE TABLE users (
  user_id bigint NOT NULL PRIMARY KEY AUTO_INCREMENT UNIQUE,
  user_alias varchar(128) NOT NULL,
  user_email varchar(320) NOT NULL UNIQUE,
  user_login varchar(128) NOT NULL UNIQUE,
  user_password char(60) NOT NULL UNIQUE,
  user_balance integer NOT NULL DEFAULT 10000,
  user_picture varchar(128) NOT NULL,
  user_createdt datetime DEFAULT CURRENT_TIMESTAMP,
  user_verified tinyint NOT NULL DEFAULT 0
);


CREATE TABLE libraries (
  user_id bigint NOT NULL,
  game_id bigint NOT NULL,
  PRIMARY KEY (user_id, game_id)
);

CREATE TABLE carts (
  user_id bigint NOT NULL,
  game_id bigint NOT NULL,
  PRIMARY KEY (user_id, game_id)
);


CREATE TABLE reviews (
  game_id bigint NOT NULL,
  user_id bigint NOT NULL,
  review_title varchar(256) NOT NULL,
  review_content text NOT NULL,
  review_score smallint NOT NULL,
  PRIMARY KEY (game_id, user_id)
);


CREATE TABLE games (
  game_id bigint NOT NULL PRIMARY KEY AUTO_INCREMENT UNIQUE,
  game_title varchar(256) NOT NULL,
  game_price int NOT NULL,
  game_desc text NOT NULL,
  game_sale float DEFAULT 0.00,
  game_releasedate DATE,
  game_active boolean DEFAULT 1
);


CREATE TABLE orders (
  order_id bigint NOT NULL PRIMARY KEY AUTO_INCREMENT UNIQUE,
  order_userid bigint NOT NULL,
  order_gid bigint NOT NULL,
  order_gtitle varchar(256) NOT NULL,
  order_price decimal NOT NULL,
  order_dt datetime NOT NULL
);


CREATE TABLE wishlists (
  game_id bigint NOT NULL,
  user_id bigint NOT NULL,
  wishlist_dt datetime NOT NULL,
  PRIMARY KEY (game_id, user_id)
);


CREATE TABLE genres (
  genre_id int NOT NULL PRIMARY KEY AUTO_INCREMENT UNIQUE,
  genre_tag varchar(128) NOT NULL
);


CREATE TABLE game_genres (
  game_id bigint NOT NULL,
  genre_id int NOT NULL,
  PRIMARY KEY (game_id, genre_id)
);


ALTER TABLE carts ADD CONSTRAINT cart_game_id_fk FOREIGN KEY (game_id) REFERENCES games (game_id);
ALTER TABLE carts ADD CONSTRAINT cart_user_id_fk FOREIGN KEY (user_id) REFERENCES users (user_id);
ALTER TABLE libraries ADD CONSTRAINT libraries_game_id_fk FOREIGN KEY (game_id) REFERENCES games (game_id);
ALTER TABLE libraries ADD CONSTRAINT libraries_user_id_fk FOREIGN KEY (user_id) REFERENCES users (user_id);
ALTER TABLE reviews ADD CONSTRAINT reviews_user_id_fk FOREIGN KEY (user_id) REFERENCES users (user_id);
ALTER TABLE wishlists ADD CONSTRAINT wishlists_game_id_fk FOREIGN KEY (game_id) REFERENCES games (game_id);
ALTER TABLE wishlists ADD CONSTRAINT wishlists_user_id_fk FOREIGN KEY (user_id) REFERENCES users (user_id);
ALTER TABLE game_genres ADD CONSTRAINT game_genres_gameid_fk FOREIGN KEY (game_id) REFERENCES games (game_id);
ALTER TABLE game_genres ADD CONSTRAINT game_genres_genreid_fk FOREIGN KEY (genre_id) REFERENCES genres (genre_id);