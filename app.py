from flask import Flask, g, flash, redirect, render_template, request, session, abort, jsonify, url_for
import os
import xlrd
import sqlite3
from PIL import Image
import requests
from io import BytesIO
import time
import math
import random

app = Flask(__name__)
imagesAPIPoint = "https://pixabay.com/api/?key=8572181-d7de3a9d607dcb04af86261ab&q=food&per_page=200"
binary = BytesIO()

loggedInSession = 'LOGGED_IN'
userKey = 'USER'

##ROUTES
@app.route("/")
def redirection(userType = None):
    ut = 'user'
    if userType:
        ut = userType

    if not session.get(loggedInSession):
        return render_template('login.html', type=ut)
    else:
        return home()

@app.route("/home")
def home():
    db = get_db()
    recipes = []
    rows = db.execute('select * \
                                            from (select recipe_id, avg(rating) as avgRating, count(*) as numRatings \
                                                        from (select * from recipes join recipe_ratings on recipes.recipe_id = recipe_ratings.recipe_id) \
                                                        group by recipe_id) \
                                            natural join recipes natural join chefs \
                                            order by avgRating desc')
    for row in rows:
        avgRating = row["avgRating"] 
        avgRating = math.floor(avgRating + 0.5)
        recipe_row = dict(row)
        recipe_row["avgRating"] = avgRating
        recipes.append(recipe_row)
    
    popular_recipes = [recipes[i] for i in range(10)]
    reg_recipes = [recipes[i] for i in range(10, len(recipes))]
    perColumn = math.floor(len(reg_recipes) / 3)
    leftOvers = len(reg_recipes) - perColumn * 3
    random.shuffle(reg_recipes)

    fav_recipe_rows = db.execute('select * from favorite_recipes where email=?', [session.get(userKey)])
    favR = []

    for row in fav_recipe_rows:
        favR.append(row["recipe_id"])

    print(favR)
    return render_template('main.html', popular=popular_recipes, recipes=reg_recipes, perColumn=perColumn, leftOvers=leftOvers, favRecipes=favR)

@app.route("/login", methods=['POST'])
def do_login():
    print("Attempt to Login!")
    db = get_db()

    EMAIL = str(request.form['lemail'])
    PASSWORD = str(request.form['lpassword'])

    print(EMAIL)
    print(PASSWORD)

    if not EMAIL or not PASSWORD:
        return redirection()

    try:
        rows = db.execute("select * from master_users where email=?",[EMAIL])
        user_row = rows.fetchone()
        
        if PASSWORD == user_row['password'] and EMAIL == user_row['email']:
            session[loggedInSession] = True
            session[userKey] = EMAIL
        else:
            flash('Incorrect username or password!')
        return redirection()

    except (sqlite3.Error, NameError, TypeError) as e:
        flash('Incorrect username or password!')
        return redirection()
    
@app.route("/sign-up", methods=['POST'])
def do_signup():
    print("Attempt To Sign Up!")
    db = get_db()

    FNAME = ''
    LNAME = ''
    RESTAURANT = ''
    EMAIL = ''
    PASSWORD = ''
    RESTAURANT = ''
    USERNAME = ''

    if(str(request.form['view']) == 'chef'):
        FNAME = str(request.form['first-name'])
        LNAME = str(request.form['last-name'])
        RESTAURANT = str(request.form['restaurant'])
        EMAIL = str(request.form['email'])
        PASSWORD = str(request.form['password'])

        try:
            db.execute('insert into master_users (email, password) values (?, ?)', [EMAIL, PASSWORD])
            db.execute('insert into chefs (email, lname, fname, restaurant) values (?, ?, ?, ?)', [EMAIL, LNAME, FNAME, RESTAURANT])
            db.commit()
        except sqlite3.Error:
            return redirection(str(request.form['view']))

    else:
        EMAIL = str(request.form['email'])
        PASSWORD = str(request.form['password'])
        USERNAME = str(request.form['username'])

        try:
            db.execute('insert into master_users (email, password) values (?, ?)', [EMAIL, PASSWORD])
            db.execute('insert into users (email, username) values (?, ?)', [EMAIL, USERNAME])
            db.commit()
        except sqlite3.Error:
            return redirection(str(request.form['view']))
    
    session[loggedInSession] = True
    session[userKey] = EMAIL
    return redirection(str(request.form['view']))

@app.route("/chef/<chef>")
def go_chef(chef):
    print(chef)
    db = get_db()
    chefrows = db.execute('select * from chefs natural join recipes where email=?',[chef])
    chefrecipes = [] 
    for row in chefrows:
        print(dict(row))
        chefrecipes.append(dict(row))
    ratingrow = db.execute('select count(*) from chef_ratings where chef_email= ?',[chef])
    chefrating = ratingrow.fetchone()[0]
    return render_template('chef-page.html', chef = chefrecipes, numrecipes = len(chefrecipes), ratings = chefrating)
    

@app.route("/recipe/<recipe>")
def go_recipe(recipe):
    print(recipe)
    return render_template('recipe-page.html')

@app.route("/profile/")
def go_profile():
    print(session.get(userKey))
    return render_template('profile-page.html')

##ROUTE FUNCTIONALITY
@app.route("/handleSwitch", methods=['POST'])
def do_switch():
    loginType = str(request.form['json'])
    print(loginType)
    return render_template('login-form.html', type=loginType)

@app.route("/handleLike", methods=['POST'])
def handle_like():
    receipe_id = request.form['json']
    shouldadd = request.form["tvalue"]

    print(shouldadd)

    user = session.get(userKey)
    db = get_db()

    if shouldadd == True:
        print("WE ARE ADDING", shouldadd)
        db.execute('insert into favorite_recipes (email, recipe_id) values (?, ?)', [user, receipe_id])
        db.commit()
    else:
        db.execute('delete from favorite_recipes where email=? and recipe_id=?', [user, receipe_id])
        db.commit()

    return jsonify({"status": "OK"}), 200

##DEV FUNCTIONS
@app.teardown_appcontext
def close_db(error):
    """Closes the database automatically when the application
    context ends."""
    print("Disconnecting from DB.")
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.cli.command("createDB")
def initDb():
    db = get_db()
    with open('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    populateDB()

##UTILITY FUNCTIONS
def connectToDB():
    print("Attempting To Connect To DB ...")
    conn = sqlite3.connect('ChefsDelight.db')
    conn.row_factory = sqlite3.Row
    print("Connected To DB ...")
    return conn

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connectToDB()
    return g.sqlite_db

def populateDB():
    db = get_db()
    print("Populating DB ...")
    excelDB = xlrd.open_workbook('ChefsDelightDataBase.xlsx')
    print("The number of worksheets are", excelDB.nsheets)

    ##master_users
    sheet = excelDB.sheet_by_index(0)
    print("Inserting into ", sheet.name)
    for i in range(1, sheet.nrows):
        db.execute("insert into master_users (email, password) values (?, ?)", 
        [sheet.row(i)[0].value, sheet.row(i)[1].value])
    db.commit()

    ##users
    sheet = excelDB.sheet_by_index(1)
    print("Inserting into ", sheet.name)
    for i in range(1, sheet.nrows):
        db.execute("insert into users (email, username) values (?, ?)", 
        [sheet.row(i)[0].value, sheet.row(i)[1].value])
    db.commit()

    ##chefs
    sheet = excelDB.sheet_by_index(2)
    print("Inserting into ", sheet.name)
    for i in range(1, sheet.nrows):
        db.execute("insert into chefs (email, lname, fname, restaurant) values (?, ?, ?, ?)", 
        [sheet.row(i)[0].value, sheet.row(i)[1].value, sheet.row(i)[2].value, sheet.row(i)[3].value])
    db.commit()

    ##recipes
    sheet = excelDB.sheet_by_index(3)
    print("Inserting into ", sheet.name)
    response = requests.get(imagesAPIPoint).json()
    print(len(response["hits"]));
    images = response["hits"]
    for i in range(1, sheet.nrows):
        response = images[i-1]["largeImageURL"]
        print("generated Image ", i)
        db.execute("insert into recipes (email, name, recipe_id, imagesrc, description, instructions) values (?, ?, ?, ?, ?, ?)", 
        [sheet.row(i)[0].value, sheet.row(i)[1].value, sheet.row(i)[2].value, response, sheet.row(i)[3].value, sheet.row(i)[4].value])
    db.commit()

    ##ingredients
    sheet = excelDB.sheet_by_index(4)
    print("Inserting into ", sheet.name)
    for i in range(1, sheet.nrows):
        try:
            db.execute("insert into ingredients (supply_name, amount, measurement, recipe_id) values (?, ?, ?, ?)", 
            [sheet.row(i)[0].value, sheet.row(i)[1].value, sheet.row(i)[2].value, sheet.row(i)[3].value])
        except sqlite3.IntegrityError:
            print('INGREDIENT DUPLICATE')
            continue
    db.commit()

    ##chef_ratings
    sheet = excelDB.sheet_by_index(5)
    print("Inserting into ", sheet.name)
    for i in range(1, sheet.nrows):
        try:
            db.execute("insert into chef_ratings (email, rating, chef_email) values (?, ?, ?)", 
            [sheet.row(i)[0].value, sheet.row(i)[1].value, sheet.row(i)[2].value])
        except sqlite3.IntegrityError:
            print('CHEF RATING DUPLICATE')
            continue
    db.commit()

    ##comments
    sheet = excelDB.sheet_by_index(6)
    print("Inserting into ", sheet.name)
    for i in range(1, sheet.nrows):
        db.execute("insert into comments (email, comment_id, comment) values (?, ?, ?)", 
        [sheet.row(i)[0].value, sheet.row(i)[1].value, sheet.row(i)[2].value])
    db.commit()

    ##recipe_ratings
    sheet = excelDB.sheet_by_index(7)
    print("Inserting into ", sheet.name)
    for i in range(1, sheet.nrows):
        try:
            db.execute("insert into recipe_ratings (email, rating, recipe_id) values (?, ?, ?)", 
            [sheet.row(i)[0].value, sheet.row(i)[1].value, sheet.row(i)[2].value])
        except sqlite3.IntegrityError:
            print('RECIPE RATING DUPLICATE')
            continue
    db.commit()

    ##favorite_recipes
    sheet = excelDB.sheet_by_index(8)
    print("Inserting into ", sheet.name)
    for i in range(1, sheet.nrows):
        db.execute("insert into favorite_recipes (email, recipe_id) values (?, ?)", 
        [sheet.row(i)[0].value, sheet.row(i)[1].value])
    db.commit()

     ##favorite_chefs
    sheet = excelDB.sheet_by_index(9)
    print("Inserting into ", sheet.name)
    for i in range(1, sheet.nrows):
        db.execute("insert into favorite_chefs (email, chef_email) values (?, ?)", 
        [sheet.row(i)[0].value, sheet.row(i)[1].value])
    db.commit()

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(port=8080)