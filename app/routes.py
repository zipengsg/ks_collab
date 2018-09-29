from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.models import User, Post, Topic, Article, Expert, TermMap
from app.forms import LoginForm, RegistrationForm, TestingButtonsForm
from app.scrapers import Twitter_Scraper, Newsplease_Scraper, NewsAPI_API
from app.utilities import Database_Cleaner

@app.route('/')
@app.route('/index')
# @login_required
def index():

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
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
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
    form = TestingButtonsForm()
    twitter_scraper = Twitter_Scraper()
    newsplease_scraper = Newsplease_Scraper()
    newsAPI_API = NewsAPI_API()
    database_cleaner = Database_Cleaner()

    if form.validate_on_submit():
        if form.update_tweets.data:
            print('updating tweets')
            twitter_scraper.update_source()
        
        if form.crawl_commoncrawl.data:
            print('crawling commoncrawl')
            newsplease_scraper.crawl_source()
        
        if form.request_newsAPI.data:
            print('requesting newsAPI')
            newsAPI_API.request_source(form.newsAPI_keyword_field.data, int(form.newsAPI_max_pages_field.data))

        if form.update_newsAPI.data:
            print('updating newsAPI')
            newsAPI_API.update_source()

        if form.crawl_fulltext_for_newsAPI.data:
            print('crawling content for newsAPI')
            newsplease_scraper.crawl_newsAPI_fulltext()
            
        if form.remove_fulltext_duplicates.data:
            print('removing fulltext duplicates')
            database_cleaner.remove_fulltext_duplicates()
        
        if form.remove_url_duplicates.data:
            print('removing url duplicates')
            database_cleaner.remove_url_duplicates()

        return redirect(url_for('test'))

    return render_template('test.html', title='Test', form=form)