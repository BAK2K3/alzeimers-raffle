import os

from flask import Flask
from flask_pymongo import PyMongo

if os.path.exists("env.py"):
    import env

import re

from flask import render_template, request, redirect, flash, url_for
from flask_login import (LoginManager, login_user,
                         logout_user, current_user, login_required)
from werkzeug.security import generate_password_hash, check_password_hash

from classes import User

# Instantiate Mongo Database
mongo = PyMongo()


# https://stackoverflow.com/questions/48653120/flask-pymongo-with-application-factory-and-blueprints
def create_app():
    app = Flask(__name__)
    app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
    app.config["PREFERRED_URL_SCHEME"] = "https"
    app.config["TESTING"] = False
    app.secret_key = os.environ.get("SECRET_KEY")
    mongo.init_app(app)
    return app


app = create_app()


# Instantiate login_manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_manager.login_view = 'index'


# Define the user_loader callback for Flask-Login
@login_manager.user_loader
def load_user(username):
    login_attempt = mongo.db.users.find_one({"username": username.lower()})
    if not login_attempt:
        return None
    return User(username=login_attempt["username"])


# Register Route
@ app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # Verify user password
        user_password = request.form.get("passwordRegister")
        password_confirmation = request.form.get("passwordConfirm")
        if not re.search("^(?=.*[^a-zA-Z]).{6,20}$", user_password):
            flash("Password format incorrect!")
            return render_template("index.html")

        if user_password != password_confirmation:
            flash("Passwords do not match!")
            return render_template("index.html")

        # check if username already exists in DB
        username_check = mongo.db.users.find_one(
            {"username": request.form.get("usernameRegister").lower()})

        # Username Validation
        if username_check:
            flash("Username already exists!")
            return redirect(url_for("index"))

        # Create a registration dictionary
        registration = {
            "username": request.form.get("usernameRegister").lower(),
            "password": generate_password_hash(user_password)
        }

        # Update DB with registration dictionary
        mongo.db.users.insert_one(registration)

        # Create an instance of User with new user, and log in
        new_user = User(username=registration['username'])
        login_user(new_user)

        # Flash and redirect
        flash("Registration Successful")
        return redirect(url_for("messages.my_voice"))


@ app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == "POST":
        # Query DB for username
        login_check = mongo.db.users.find_one(
            {"username": request.form.get("usernameLogin").lower()})

        # Check username exists and password matches
        if login_check and check_password_hash(
                login_check["password"],
                request.form.get("passwordLogin")):

            # Create an instance of User class, log them in, and redirect
            existing_user = User(username=login_check['username'])
            login_user(existing_user)
            flash(f"Welcome, {current_user.username}")
            return redirect(url_for("index"))

        else:
            #  Inform user that credentials are incorrect
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("index.html")


@ app.route('/logout')
@ login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@ app.route('/')
def index():
    return render_template("index.html")


@ app.route('/admin')
def admin():
    return render_template("admin.html")


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
