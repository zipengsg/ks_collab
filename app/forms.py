from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User

class LoginForm(FlaskForm):
    """
    LoginForm houses all interactive fields associated with web form used
        for the login page.
    """
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """
    RegistrationForm houses all interactive fields associated with the
        web form used for the account registration page.
    """
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
    """
    TestingButtonsForm houses all interactive fields associated with the web
        form used for the admin unit testing page.
    """
    # utilities
    remove_fulltext_duplicates = SubmitField('Remove Fulltext Duplicates')
    remove_url_duplicates = SubmitField('Remove URL Duplicates')

    # data collection
    update_tweets = SubmitField('Update Tweets')
    crawl_commoncrawl = SubmitField('Crawl CommonCrawl')

    newsapi_keyword_field = StringField('Keywords')
    newsapi_max_pages_field = StringField('Max Pages')
    request_newsapi = SubmitField('Request NewsAPI')

    update_newsapi = SubmitField('Update NewsAPI')
    crawl_fulltext_for_newsapi = SubmitField('Crawl Content for NewsAPI')

    