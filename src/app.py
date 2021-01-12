from flask import Flask, redirect, url_for, session, request, render_template, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user, LoginManager, login_required, login_user, logout_user
from sqlalchemy.orm.exc import NoResultFound
import tweepy
import time
import random
from functools import wraps

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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Bu sayfayı görüntülemek için lütfen giriş yapın.', 'danger')
            return redirect(url_for('auth'))

    return decorated_function

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
        username = api.me().screen_name
        return render_template("index.html", username=username)
    else:
        return render_template("index.html")


@app.route('/unfollowers', methods = ['GET','POST'])
def unfollowers():
    # session['progress'] = True
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
        api = tweepy.API(auth, wait_on_rate_limit=True)
        me = api.me()
        if request.method == "POST":
            favs_ids = []
            for favorite in tweepy.Cursor(api.favorites).items():
                api.destroy_favorite(favorite.id)
            times = time.time()-starttime
            return render_template('features/favorites.html', favs_ids=favs_ids, times=times, me=me)
        else:
            return render_template('features/favorites.html', me=me)
    else:
        return render_template('features/favorites.html')

@app.route('/delete_tweets', methods = ['GET','POST'])
def delete_tweets():
    if 'token' in session:
        starttime = time.time()
        token, token_secret = session['token']
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
        auth.set_access_token(token, token_secret)
        api = tweepy.API(auth)
        me = api.me()
        if request.method == "POST":
            timeline = api.user_timeline()
            tweets =[]
            for tweet in tweepy.Cursor(api.user_timeline).items():
                tweets.append(tweet)
            times = time.time()-starttime
            return render_template('features/delete_tweets.html', tweets=tweets, me=me)
        else:
            return render_template('features/delete_tweets.html', me=me)
    else:
        return render_template('features/delete_tweets.html',me=me)

@app.route('/test', methods = ['GET','POST'])
def test():
    if request.method == "POST":
        if 'token' in session:
            starttime = time.time()
            token, token_secret = session['token']
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback)
            auth.set_access_token(token, token_secret)
            api = tweepy.API(auth)
            favs_text = []
            for favorite in tweepy.Cursor(api.favorites, wait_on_rate_limit=True, wait_on_rate_limit_notify=True).items(limit=50):
                favs_text.append(favorite._json)
            times = time.time()-starttime
            return render_template('features/test.html',times=times, favs_text=favs_text)
    else:
        return render_template('features/test.html')


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


@app.route('/progress')
def progress():
	def generate():
		x = 0
		
		while x <= 99:
			yield "data:" + str(x) + "\n\n"
			x = x + random.randint(1,20)
			time.sleep(random.randint(1, 3))
	return Response(generate(), mimetype= 'text/event-stream')


@app.route('/about/')
def about():
    return "about"


@app.route('/privacy_policy/')
def privacy_policy():
    return "privacy_policy"



@app.route('/pricing/')
def pricing():
    return "pricing"