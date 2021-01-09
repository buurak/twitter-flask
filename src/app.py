from flask import Flask, redirect, url_for
from flask_dance.contrib.twitter import make_twitter_blueprint, twitter
from flask_sqlalchemy import SQLALchemy
from flask_login import UserMixin
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin

app = Flask(__name__)

app.config.from_object("config")
app.secret_key = app.config["SECRET_KEY"]
app.sqlalchemy_database_uri = app.config["SQLALCHEMY_DATABASE_URI"]


CONSUMER_KEY = app.config["CONSUMER_KEY"]
CONSUMER_SECRET = app.config["CONSUMER_SECRET"]
ACCESS_TOKEN = app.config["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = app.config["ACCESS_TOKEN_SECRET"]


twitter_blueprint = make_twitter_blueprint(
    api_key=CONSUMER_KEY,
    api_secret=CONSUMER_SECRET,
)

app.register_blueprint(twitter_blueprint, url_prefix="/twitter_login")

# @app.route("/")
# def hello_world():
#     return "Hello, World!"


@app.route("/twitter")
def twitter_login():
    if not twitter.authorized:
        return redirect(url_for('twitter.login'))

    account_info = twitter.get('account/settings.json')

    if account_info.ok:
        account_info_json = account_info.json()

        return f"<h1>Your twitter username: @{account_info_json}</h1>"
    
    return '<h1>Request failed!</h1>'