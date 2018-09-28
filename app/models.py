from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    
    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

# Association table to enable many-to-many relationship betwee topics and articles
topic_article_at = db.Table('topic_article_at', 
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id')),
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'))
)

# Association table to enable many-to-many relationship betwee topics and experts
topic_expert_at = db.Table('topic_expert_at', 
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id')),
    db.Column('expert_id', db.Integer, db.ForeignKey('expert.id'))
)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(128), index=True, unique=True)
    topic_genre = db.Column(db.String(64))
    topic_createdate = db.Column(db.DateTime, index=True)

    articles = db.relationship("Article", secondary=topic_article_at, back_populates="topics")
    experts = db.relationship("Expert", secondary=topic_expert_at, back_populates="topics")

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_type = db.Column(db.String(64))
    source_name = db.Column(db.String(64), index=True)
    article_author = db.Column(db.String(64), index=True)
    article_publishdate = db.Column(db.DateTime, index=True)
    article_wordcount = db.Column(db.Integer)
    article_title = db.Column(db.String(), index=True)
    article_summary = db.Column(db.String(1000))
    article_fulltext = db.Column(db.String())
    article_url = db.Column(db.String(128), index=True)

    topics = db.relationship("Topic", secondary=topic_article_at, back_populates="articles")

class Expert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expert_name = db.Column(db.String(64), index=True, unique=True)
    expert_affiliation = db.Column(db.String(128), index=True)

    topics = db.relationship("Topic", secondary=topic_expert_at, back_populates="experts")

class TermMap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(64), index=True, unique=True)
    map_idx = db.Column(db.Integer, index=True)

