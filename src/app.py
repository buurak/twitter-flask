from flask import Flask, redirect, url_for, session
from flask_dance.contrib.twitter import make_twitter_blueprint, twitter
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user, LoginManager, login_required, login_user, logout_user
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin, SQLAlchemyStorage
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)

app.config.from_object("config")
app.secret_key = app.config["SECRET_KEY"]

CONSUMER_KEY = app.config["CONSUMER_KEY"]
CONSUMER_SECRET = app.config["CONSUMER_SECRET"]
ACCESS_TOKEN = app.config["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = app.config["ACCESS_TOKEN_SECRET"]


twitter_blueprint = make_twitter_blueprint(
    api_key=CONSUMER_KEY,
    api_secret=CONSUMER_SECRET,
)

app.register_blueprint(twitter_blueprint, url_prefix="/twitter_login")


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://///home/ilteriskeskin/Belgeler/twitter-flask/src/database.db"
db = SQLAlchemy(app)

login_manager = LoginManager(app)

from models import User, OAuth


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
twitter_blueprint.backend = SQLAlchemyStorage(OAuth, db.session, user=current_user)


@app.route("/")
@login_required
def home():
    return f"Hello, {current_user.username}"

@app.route("/logout/")
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('home'))


@app.route("/twitter")
def twitter_login():
    if not twitter.authorized:
        return redirect(url_for('twitter.login'))

    account_info = twitter.get('account/settings.json')
    account_info_json = account_info.json()

    return f"<h1>Your twitter username: @{account_info_json['screen_name']}</h1>"
    

@oauth_authorized.connect_via(twitter_blueprint)
def twitter_logged_in(blueprint, token):
    account_info = blueprint.session.get('account/settings.json')

    if account_info.ok:
        account_info_json = account_info.json()
        username = account_info_json['screen_name']

        query = User.query.filter_by(username=username)

        try:
            user = query.one()
            print("AAAAAAAAAAAAA: ", user)
        except NoResultFound:
            user = User(username=username)
            print("BBBBBBBBBBBB: ", user)
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
