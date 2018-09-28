from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class TestingButtonsForm(FlaskForm):
    # utilities
    remove_fulltext_duplicates = SubmitField('Remove Fulltext Duplicates')
    remove_url_duplicates = SubmitField('Remove URL Duplicates')

    # data collection
    update_tweets = SubmitField('Update Tweets')
    crawl_commoncrawl = SubmitField('Crawl CommonCrawl')

    newsAPI_keyword_field = StringField('Keywords')
    newsAPI_max_pages_field = StringField('Max Pages')
    request_newsAPI = SubmitField('Request NewsAPI')

    update_newsAPI = SubmitField('Update NewsAPI')
    crawl_fulltext_for_newsAPI = SubmitField('Crawl Content for NewsAPI')

    