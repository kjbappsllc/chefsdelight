from flask import Flask, g
import os
import xlrd
import sqlite3
from PIL import Image
import requests
from io import BytesIO
import time

app = Flask(__name__)
imagesAPIPoint = "https://pixabay.com/api/?key=8572181-d7de3a9d607dcb04af86261ab&q=food&per_page=200"
binary = BytesIO()

##ROUTES
@app.route("/")
def hello():
    return "Hello World!"

##DEV FUNCTIONS
@app.teardown_appcontext
def close_db(error):
    """Closes the database automatically when the application
    context ends."""
    print("Disconnecting from DB.")
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.cli.command("testImage")
def getImage():
    db = get_db()
    rows = db.execute("select * from recipes where recipe_id = 2")
    rowlist = rows.fetchall()

    for row in rowlist:
        print(row["email"])
        Image.open(BytesIO(row["image"])).save("key.jpeg", format="JPEG")

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
        hexData = None
        response = requests.get(images[i]["largeImageURL"])
        img = Image.open(BytesIO(response.content))
        img = img.resize((500,500), Image.ANTIALIAS)
        if img.mode in ('RGBA', 'LA'):
            print("IS RGBA IMAGE")
            background = Image.new(img.mode[:-1], img.size, '#fff')
            background.paste(img, img.split()[-1])
            img = background
        img.save(binary, format="JPEG")
        hexData = binary.getvalue()
        print("generated Image ", i)
        db.execute("insert into recipes (email, name, recipe_id, image) values (?, ?, ?, ?)", 
        [sheet.row(i)[0].value, sheet.row(i)[1].value, sheet.row(i)[2].value, hexData])
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
    app.run()