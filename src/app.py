from flask import Flask, redirect, url_for, session, request, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user, LoginManager, login_required, login_user, logout_user
from sqlalchemy.orm.exc import NoResultFound
import tweepy, time

from forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.config.from_object("config")
app.secret_key = app.config["SECRET_KEY"]

CONSUMER_KEY = app.config["CONSUMER_KEY"]
CONSUMER_SECRET = app.config["CONSUMER_SECRET"]
ACCESS_TOKEN = app.config["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = app.config["ACCESS_TOKEN_SECRET"]

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/brk/Desktop/twitter-flask/src/database.db'
db = SQLAlchemy(app)
from models import User


consumer_key = CONSUMER_KEY
consumer_secret = CONSUMER_SECRET
callback = 'http://127.0.0.1:5000/callback'

def diff(li1, li2):
    return (list(list(set(li1)-set(li2)) + list(set(li2)-set(li1))))

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


@app.route('/')
def home():
    if 'token' in session:
        starttime = time.time()
        token, token_secret = session['token']
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
        auth.set_access_token(token, token_secret)
        api = tweepy.API(auth)
        return render_template("index.html")
    else:
        return render_template("index.html")


@app.route('/unfollowers', methods = ['GET','POST'])
def unfollowers():
    if 'token' in session:
        starttime = time.time()
        token, token_secret = session['token']
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
        auth.set_access_token(token, token_secret)
        api = tweepy.API(auth)    

        followers_ids = api.followers_ids()
        followed_ids = api.friends_ids()
        difference_list = diff(followed_ids, followers_ids)
        counter = 0
        counter_2 = 0
        a = []
        for i in range(len(difference_list)//100+1):
            counter = i*100
            counter_2 += 100
            a.append(api.lookup_users(difference_list[counter:counter_2]))
        nons_list = []
        for i in a:
            for j in i:
                nons_list.append(j._json['id'])

        unfollowers_ids_list =list(set(nons_list) - set(followers_ids))
        counter_3 = 0
        counter_4 = 0
        b=[]
        for i in range(len(unfollowers_ids_list)//100+1):
            counter_3 = i*100
            counter_4 += 100
            b.append(api.lookup_users(unfollowers_ids_list[counter_3:counter_4]))
        unfollowers_list = []
        times = time.time()-starttime
        for i in b:
            for j in i:
                unfollowers_list.append(j._json['screen_name'])
            return render_template("features/unfollowers.html", unfollowers_list=unfollowers_list, times=times)


@app.route('/favorites', methods = ['GET','POST'])
def favorites():
    if 'token' in session:
        starttime = time.time()
        token, token_secret = session['token']
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
        auth.set_access_token(token, token_secret)
        api = tweepy.API(auth)
        favs = api.favorites(count=250)
        favs_list = []
        me = api.me()
        for i in favs:
            favs_list.append(i._json['text'])
        times = time.time()-starttime
        return render_template('features/favorites.html', favs=favs_list, times=times, me=me)



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
    return redirect(url_for('home'))


