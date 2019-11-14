from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, make_response
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_table import Table, Col
import datetime
import uuid


import unittest, os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite/webapp.db'
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
userList = []
session = False
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

class LoginHistoryTable(Table):
    thisdict = {
        "id": "login_id",
    }
    logindict = {
        "id" : "login_time"
    }
    logoutdict = {
        "id" : "logout_time"
    }
    id = Col('id', td_html_attrs=thisdict)
    username = Col('Username')
    login_time = Col('Login Time', td_html_attrs=logindict)
    logout_time = Col('Logout Time', td_html_attrs=logoutdict)



class user:
  def __init__(self, username, password, twofactor):
    self.username = username
    self.password = password
    self.twofactor = twofactor

    # getter method
    def get_username(self):
        return self.username

    def get_password(self):
        return self.password

class response:
    def __init__(self, input, response):
        self.input = input
        self.response = response

class LoginHistory(db.Model):
    id=db.Column(db.String(), primary_key=True)
    username = db.Column(db.String(), nullable=False)
    login_time = db.Column(db.TIMESTAMP(120), unique=False, nullable=False)
    logout_time = db.Column(db.TIMESTAMP(120), unique=False, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


class Users(db.Model):
    username = db.Column(db.String(80), primary_key=True, unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False, nullable=False)
    twofactor = db.Column(db.String(80), unique=False, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/spell_check", methods=["GET", "POST"])
def spell_check():
    if session == False:
        return redirect(url_for("login"))
    else:
        data = response
        if request.method == "POST":
            inputtext = request.form["inputtext"]
            data.input = inputtext
            from subprocess import call
            call(["./a.out"])

            r = make_response(render_template("spell_check.html", data = data))
            r.headers.set('Content-Security-Policy', "default-src 'self'")
            return r
        r = make_response(render_template("spell_check.html", data=data))
        r.headers.set('Content-Security-Policy', "default-src 'self'")
        return r


def findUser(user_name):
    return Users.query.filter_by(username=user_name).first()

def createUser(user_name, pword, twofact):
    if findUser(user_name) is None:
        user = Users(id="",username=user_name, password=pword, twofactor=twofact)
        db.session.add(user)
        db.session.commit()
        return True
    else:
        return False

def logLogin(user_name):
    id = str(uuid.uuid1())
    event = LoginHistory(id=id, username=user_name, login_time=datetime.datetime.now())
    db.session.add(event)
    db.session.commit()

def loginUser(user_name, pword, twofact):
    theUser = findUser(user_name)
    if theUser is not None:
        if theUser.password == pword and theUser.twofactor == twofact:
            global session
            session = True
            logLogin(user_name)
            return True
        else:
            return False

@app.route("/login", methods=["GET", "POST"])
def login():
    data = ""
    if request.method == "POST":
        uname = request.form["uname"]
        pword = request.form["pword"]
        twofact = request.form["2fa"]
        theUser = findUser(uname)
        if loginUser(uname, pword, twofact):
            global session
            session = True
            data = "success"
    r = make_response(render_template("login.html", data = data))
    r.headers.set('Content-Security-Policy', "default-src 'self'")
    return r

@app.route("/login_history", methods=["GET", "POST"])
def history():
    if request.method == "POST":
        # Or, more likely, load items from your database with something like
        history = LoginHistory.query.all()
        # Populate the table
        table = LoginHistoryTable(history)
        r = make_response(render_template("login_history.html", data=table))
        r.headers.set('Content-Security-Policy', "default-src 'self'")
        return r
    r = make_response(render_template("login_history.html"))
    r.headers.set('Content-Security-Policy', "default-src 'self'")
    return r

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form['uname']
        pword = request.form['pword']
        twofact = request.form['2fa']
        register = user(username=uname, password=pword, twofactor=twofact)
        global userList
        success = "Account creation failure"
        result = createUser(uname, pword, twofact)
        if result is True:
            success = "Account creation success"
        r = make_response(render_template("register.html", data=success))
        r.headers.set('Content-Security-Policy', "default-src 'self'")
        return r

    r = make_response(render_template("register.html"))
    r.headers.set('Content-Security-Policy', "default-src 'self'")
    return r


if __name__ == "__main__":
    app.run(debug=True)

