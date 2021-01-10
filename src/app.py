from flask import Flask, redirect, url_for, session, request, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user, LoginManager, login_required, login_user, logout_user
from sqlalchemy.orm.exc import NoResultFound
import tweepy

from forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.config.from_object("config")
app.secret_key = app.config["SECRET_KEY"]

CONSUMER_KEY = app.config["CONSUMER_KEY"]
CONSUMER_SECRET = app.config["CONSUMER_SECRET"]
ACCESS_TOKEN = app.config["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = app.config["ACCESS_TOKEN_SECRET"]

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/ilteriskeskin/Belgeler/twitter-flask/src/database.db'
db = SQLAlchemy(app)
from models import User


consumer_key = CONSUMER_KEY
consumer_secret = CONSUMER_SECRET
callback = 'http://127.0.0.1:5000/callback'

@app.route('/auth')
def auth():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
    url = auth.get_authorization_url()
    session['request_token'] = auth.request_token
    return redirect(url)


@app.route('/callback')
def twitter_callback():
    request_token = session['request_token']
    del session['request_token']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
    auth.request_token = request_token
    verifier = request.args.get('oauth_verifier')
    auth.get_access_token(verifier)
    session['token'] = (auth.access_token, auth.access_token_secret)

    return redirect(url_for('home'))


# @app.route('/app')
# def request_twitter():
#     token, token_secret = session['token']
#     auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
#     auth.set_access_token(token, token_secret)
#     api = tweepy.API(auth)

#     return render_template("index.html")


@app.route('/')
def home():
    if session['token']:
        token, token_secret = session['token']
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
        auth.set_access_token(token, token_secret)
        api = tweepy.API(auth)

        followers = api.me()

        return render_template("index.html", followers=followers)
    else:
        return render_template("index.html")


@app.route('/login/', methods = ['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate:
        user = User.query.filter_by(email = form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                flash("Başarıyla Giriş Yaptınız", "success")
                
                session['logged_in'] = True
                session['email'] = user.email 

                return redirect(url_for('home'))
            else:
                flash("Kullanıcı Adı veya Parola Yanlış", "danger")
                return redirect(url_for('login'))

    return render_template('auth/login.html', form = form)


@app.route('/register/', methods = ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(name = form.name.data, username = form.username.data, email = form.email.data, password = hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Başarılı bir şekilde kayıt oldunuz', 'success')
        return redirect(url_for('login'))
    else:
        return render_template('auth/register.html', form = form)

@app.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('login'))