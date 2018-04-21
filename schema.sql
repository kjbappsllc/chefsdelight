DROP TABLE IF EXISTS master_users;
CREATE TABLE master_users (
    email VARCHAR(30) NOT NULL,
    password VARCHAR(50) NOT NULL,
    PRIMARY KEY(email)
);
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    email VARCHAR(30) REFERENCES master_users(email) NOT NULL,
    username VARCHAR(20) NOT NULL,
    PRIMARY KEY(email)
);
DROP TABLE IF EXISTS chefs;
CREATE TABLE chefs (
    email VARCHAR(30) REFERENCES master_users(email) NOT NULL,
    lname VARCHAR(20) NOT NULL,
    fname VARCHAR(20) NOT NULL,
    restaurant VARCHAR(40) NOT NULL,
    PRIMARY KEY(email)
);
DROP TABLE IF EXISTS recipes;
CREATE TABLE recipes (
    email VARCHAR(30) REFERENCES chefs(email) NOT NULL,
    name VARCHAR(40) NOT NULL,
    recipe_id INTEGER NOT NULL,
    imagesrc VARCHAR(50),
    description VARCHAR(500),
    instructions VARCHAR(750),
    PRIMARY KEY(recipe_id)
);
DROP TABLE IF EXISTS ingredients;
CREATE TABLE ingredients (
    supply_name VARCHAR(30) NOT NULL,
    amount DECIMAL NOT NULL,
    measurement VARCHAR(10) NOT NULL,
    recipe_id INT REFERENCES recipes(recipe_id) NOT NULL,
    PRIMARY KEY(supply_name, recipe_id)
);
DROP TABLE IF EXISTS chef_ratings;
CREATE TABLE chef_ratings (
    email VARCHAR(30) REFERENCES master_users(email) NOT NULL,
    rating SMALLINT NOT NULL,
    chef_email VARCHAR(40) REFERENCES chefs(email) NOT NULL,
    PRIMARY KEY(email, chef_email)
);
DROP TABLE IF EXISTS comments;
CREATE TABLE comments (
    email VARCHAR(30) REFERENCES master_users(email) NOT NULL,
    comment_id INT NOT NULL,
    comment VARCHAR(500) NOT NULL,
    PRIMARY KEY(comment_id)
);
DROP TABLE IF EXISTS recipe_ratings;
CREATE TABLE recipe_ratings (
    email VARCHAR(30) REFERENCES master_users(email) NOT NULL,
    rating SMALLINT NOT NULL,
    recipe_id INT REFERENCES recipes(recipe_id) NOT NULL,
    PRIMARY KEY(email, recipe_id)
);
DROP TABLE IF EXISTS favorite_recipes;
CREATE TABLE favorite_recipes (
    email VARCHAR(30) REFERENCES master_users(email) NOT NULL,
    recipe_id INT REFERENCES recipes(recipe_id) NOT NULL,
    PRIMARY KEY(email, recipe_id)
);
DROP TABLE IF EXISTS favorite_chefs;
CREATE TABLE favorite_chefs (
    email VARCHAR(30) REFERENCES master_users(email),
    chef_email VARCHAR(30) REFERENCES chefs(email),
    PRIMARY KEY(email, chef_email)
);