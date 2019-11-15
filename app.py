from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, make_response
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_table import Table, Col
from flask import Flask, Response, redirect, url_for, request, session, abort
import datetime
import uuid
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user

import unittest, os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite/webapp.db'
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
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
    login_time = Col('Login Time', td_html_attrs={"id" : "login_time"})
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
    id=db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(), nullable=False)
    login_time = db.Column(db.TIMESTAMP(120), unique=False, nullable=False)
    logout_time = db.Column(db.TIMESTAMP(120), unique=False, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

class QueryHistory(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer(), nullable=False)
    input = db.Column(db.String())
    result = db.Column(db.String())


    def __repr__(self):
        return '<User %r>' % self.username


class Users(db.Model):
    username = db.Column(db.String(), unique=True, primary_key=True)
    password = db.Column(db.String(120), unique=False, nullable=False)
    twofactor = db.Column(db.String(80), unique=False, nullable=False)
    userid = db.Column(db.Integer(), unique=True)

    def __repr__(self):
        return '<User %r>' % self.username

class User(UserMixin):
    pass

def getUserId(username):
    return Users.query.filter_by(username=username).first().userid

def getUserPassword(username):
    return Users.query.filter_by(username=username).first().password

def getUserTwoFactor(username):
    return Users.query.filter_by(username=username).first().twofactor

@login_manager.user_loader
def load_user(userid):
    user = User()
    user.id = userid
    return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('uname')
    password = request.form.get('pword')
    twofactor = request.form.get('2fa')

    theUser = findUser(username)

    if theUser is not None:
        user = User()
        user.id = getUserId(username)
        user.username = username
        if theUser.password == password and theUser.twofactor == twofactor:
            logLogin(username)
            return user
        return

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/test')
@login_required
def home():
    return Response("Hello World!")

def findUser(user_name):
    return Users.query.filter_by(username=user_name).first()

def createUser(user_name, pword, twofact):
    if findUser(user_name) is None:
        user = Users(username=user_name, password=pword, twofactor=twofact)
        db.session.add(user)
        db.session.commit()
        return True
    else:
        return False

def logLogin(user_name):
    event = LoginHistory(username=user_name, login_time=datetime.datetime.now())
    db.session.add(event)
    db.session.commit()

def logQuery(userId, query, response):
    event = QueryHistory(userid=userId, input=query, result=response)
    db.session.add(event)
    db.session.commit()

@app.route("/login", methods=["GET", "POST"])
def login():
    data = ""
    if request.method == 'POST':
        username = request.form['uname']
        password = request.form['pword']
        twofact  = request.form['2fa']
        if password == getUserPassword(username) and twofact == getUserTwoFactor(username):
            id = getUserId(username)
            user = User()
            user.id = id
            login_user(user)
            data = "success"
#            return redirect(request.args.get("next"))
    r = make_response(render_template("login.html", data = data))
    return r

@app.route("/login_history", methods=["GET", "POST"])
def login_history():
    if request.method == "POST":
        # Or, more likely, load items from your database with something like
        history = LoginHistory.query.all()
        r = make_response(render_template("login_history.html", data=history))
        r.headers.set('Content-Security-Policy', "default-src 'self'")
        return r
    r = make_response(render_template("login_history.html"))
    r.headers.set('Content-Security-Policy', "default-src 'self'")
    return r


@app.route("/history", methods=["GET", "POST"])
@login_required
def query_history():
        history = QueryHistory.query.filter_by(userid=current_user.id)
        # Populate the table
        r = make_response(render_template("history.html", data=history))
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



@app.route("/spell_check", methods=["GET", "POST"])
@login_required
def spell_check():
        data = response
        if request.method == "POST":
            currentUser = current_user
            currentUserId = currentUser.id
            inputtext = request.form["inputtext"]
            data.input = inputtext
            from subprocess import call
            #output = call(["./a.out"])
            output = ""
            logQuery(currentUserId, inputtext, output)
            r = make_response(render_template("spell_check.html", data = data))
            r.headers.set('Content-Security-Policy', "default-src 'self'")
            return r
        r = make_response(render_template("spell_check.html", data=data))
        r.headers.set('Content-Security-Policy', "default-src 'self'")
        return r


if __name__ == "__main__":
    app.run(debug=True)

