from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.models import User, Post, Topic, Article, Expert, TermMap
from app.forms import LoginForm, RegistrationForm, TestingButtonsForm
from app.scrapers import TwitterScraper, NewspleaseScraper, NewsApiApi
from app.utilities import DatabaseCleaner

# pylint: disable=no-member
# pylint: disable=singleton-comparison
# pylint: disable=no-self-use

@app.route('/')
@app.route('/index')
# @login_required
def index():
    """
    index function details all the potential interactions the client may
        have with the /index page of the web app.
    At the moment, index function acts as a placeholder for the home page.
    """
    user = {'username': 'Miguel'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template("index.html", title='Home Page', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    login function presents the client with an interface to sign into the
        web app.
    At the moment, login function acts as a placeholder for the login page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    """
    logout function logs out the user.
    """
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    register function presents the client with a web form to register an account
        on the web app.
    At the moment, register function acts as a placeholder for the registration
        page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/test', methods=['GET', 'POST'])
def test():
    """
    test function presents a temporary admin interface that allows developers
        to call functions and conduct unit testing.
    """
    form = TestingButtonsForm()
    twitter_scraper = TwitterScraper()
    newsplease_scraper = NewspleaseScraper()
    newsapi_api = NewsApiApi()
    database_cleaner = DatabaseCleaner()

    if form.validate_on_submit():
        if form.update_tweets.data:
            print('updating tweets')
            twitter_scraper.update_source()
        
        if form.crawl_commoncrawl.data:
            print('crawling commoncrawl')
            newsplease_scraper.crawl_source()
        
        if form.request_newsapi.data:
            print('requesting newsAPI')
            newsapi_api.request_source(form.newsapi_keyword_field.data,
                                       int(form.newsapi_max_pages_field.data))

        if form.update_newsapi.data:
            print('updating newsAPI')
            newsapi_api.update_source()

        if form.crawl_fulltext_for_newsapi.data:
            print('crawling content for newsAPI')
            newsplease_scraper.crawl_newsapi_fulltext()
            
        if form.remove_fulltext_duplicates.data:
            print('removing fulltext duplicates')
            database_cleaner.article_remove_fulltext_duplicates()
        
        if form.remove_url_duplicates.data:
            print('removing url duplicates')
            database_cleaner.article_remove_url_duplicates()

        if form.populate_source_from_article.data:
            print('populating source table from existing articles')
            database_cleaner.populate_source_from_articles()

        return redirect(url_for('test'))

    return render_template('test.html', title='Test', form=form)