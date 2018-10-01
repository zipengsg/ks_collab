from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login

# pylint: disable=no-member
# pylint: disable=singleton-comparison
# pylint: disable=no-self-use

@login.user_loader
def load_user(id):
    """
    load_user tells Flask to load a user from the User table in the database.
    """
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    """
    User class abstracts the User table for sqlalchemy.
    User class is not used actively yet in the kaleidoscope app.
    User class is built as a demo when following examples through the tutorial:
    https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world
    """
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
    """
    Post class abstracts the Post table for sqlalchemy
    Post class is not used actively yet in the kaleidoscope app.
    Post class is built as a demo when following examples through the tutorial:
    https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world
    """
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
    """
    Topic class abstracts the Topic table for sqlalchemy.
    Topic class contains data fields characterizing the automatically generated topics
        from the articles within the Article table.
    Topic shares a many-to-many relationship with Article and Expert
    """
    id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(128), index=True, unique=True)
    topic_genre = db.Column(db.String(64))
    topic_createdate = db.Column(db.DateTime, index=True)

    articles = db.relationship("Article", secondary=topic_article_at, back_populates="topics")
    experts = db.relationship("Expert", secondary=topic_expert_at, back_populates="topics")

class Article(db.Model):
    """
    Article class abstracts the Article table for sqlalchemy.
    Article class contains data fields characterizing each article collected from the
        various sources (standardized format for articles from all sources).
    Article class shares a many-to-many relationship with Topic.
    Article class shares a many-to-one relationship with Source.
    """
    id = db.Column(db.Integer, primary_key=True)
    article_author = db.Column(db.String(64), index=True)
    article_publishdate = db.Column(db.DateTime, index=True)
    article_wordcount = db.Column(db.Integer)
    article_title = db.Column(db.String(), index=True)
    article_summary = db.Column(db.String(1000))
    article_fulltext = db.Column(db.String())
    article_url = db.Column(db.String(128), index=True)
    article_status = db.Column(db.String(128), index=True)

    topics = db.relationship("Topic", secondary=topic_article_at, back_populates="articles")
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'))
    source = db.relationship("Source", back_populates="articles")

class Expert(db.Model):
    """
    Expert class abstracts the Expert table for sqlalchemy.
    Expert class contains data fields characterzing each expert identified based
        on article authorship, comments, or referral.
    Expert class shares a many-to-many relationship with Topic.
    """
    id = db.Column(db.Integer, primary_key=True)
    expert_name = db.Column(db.String(64), index=True)
    expert_affiliation = db.Column(db.String(128), index=True)

    topics = db.relationship("Topic", secondary=topic_expert_at, back_populates="experts")

class Source(db.Model):
    """
    Introduced 9/29/2018; still needs to migrate source_type and source_name columns
        from Article over to this table
    Source class abstracts the Source table for sqlalchemy.
    Source contains data fields characterizing each source we reference when
        collecting data.
    """
    id = db.Column(db.Integer, primary_key=True)
    source_type = db.Column(db.String(64))
    source_name = db.Column(db.String(64), index=True)
    source_url = db.Column(db.String(128), index=True)
    source_description = db.Column(db.String(1000))
    source_statistics = db.Column(db.String)

    articles = db.relationship("Article", back_populates="source")

class TermMap(db.Model):
    """
    TermMap class abstracts teh TermMap table for sqlalchemy.
    TermMap serves as a dictionary that maps terms to indices within the TF-IDF matrix.
    """
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(64), index=True, unique=True)
    map_idx = db.Column(db.Integer, index=True)

