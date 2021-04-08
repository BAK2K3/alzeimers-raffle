import os

from flask import Flask
from flask_pymongo import PyMongo

if os.path.exists("env.py"):
    import env

import re
from flask import render_template, request, redirect, flash, url_for


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


@ app.route('/')
def index():
    return render_template("index.html")


@ app.route('/admin')
def admin():

    prizes = list(mongo.db.prizes.find())

    # Obtain Ticket Data
    ticket_data = list(mongo.db.tickets.find())
    
    # Create Ticket List and convert data to list
    ticket_list = []
    for entry in ticket_data:
        ticket_list.append(entry["Name"])
    
    total_tickets = len(ticket_list)
    
    # Create a unique set from list
    ticket_set = set(ticket_list)

    # Create ticket dictionary
    tickets_dictionary = {}

    for unique_entry in ticket_set:
        tickets_dictionary[unique_entry] = ticket_list.count(unique_entry)

    print(tickets_dictionary)

    return render_template("admin.html", prizes=prizes,
                           tickets_dictionary=tickets_dictionary,
                           total_tickets=total_tickets)


@ app.route('/select')
def select():
    return render_template("select.html")


@app.route('/insert_prize', methods=["GET", "POST"])
def insert_prize():
    new_prize = request.form.get("prizeinput")
    mongo.db.prizes.insert_one({"prize": new_prize})
    return redirect(url_for("admin"))


@app.route('/insert_ticket', methods=["GET", "POST"])
def insert_ticket():
    ticket_name = request.form.get("ticketname")
    ticket_number = request.form.get("ticketnumber")
    for i in range(int(ticket_number)):
        mongo.db.tickets.insert_one({"Name": ticket_name})
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
