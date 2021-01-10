from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name= db.Column(db.String(15), unique=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    access_token = db.Column(db.String(300), unique=True)
    access_token_secret = db.Column(db.String(300), unique=True)
    password = db.Column(db.String(25), unique=True)
