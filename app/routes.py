from flask import render_template, flash, redirect, url_for, request, send_from_directory, jsonify
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

# host static content in the assets directory
# TODO: don't host this using flask since it's super inefficient (use nginx instead)
@app.route('/assets/<path:path>')
def send_assets(path):
    return send_from_directory('assets', path)

@app.route('/assets-landing/<path:path>')
def send_assets_landing(path):
    return send_from_directory('assets-landing', path);

@app.route('/')
@app.route('/index')
def index():
    """
    home page
    """
    return render_template("frontend/landing.html", title='Home Page')

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
    return render_template('frontend/login-and-register.html', title='Sign In', form=form)

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
    return render_template('login-and-register.html', title='Register', form=form)


@app.route('/admin', methods=['GET'])
def admin():
    return render_template('backend/admin.html', title='Admin')

@app.route('/admin/sources/tweets/update', methods=['POST'])
def update_tweets():
    twitter_scraper = TwitterScraper()
    data = twitter_scraper.update_source()
    return jsonify(data);

@app.route('/admin/sources/newsplease/crawl', methods=['POST'])
def crawl_newsplease():
    newsplease_scraper = NewspleaseScraper()
    data = newsplease_scraper.crawl_source()
    return jsonify(data);    

@app.route('/admin/sources/newsapi/request', methods=['POST'])
def request_newsapi():
    newsapi_api = NewsApiApi()
    data = newsapi_api.request_source(request.form['newsapi_keyword'], int(request.form(newsapi_max_pages)));
    return jsonify(data);

@app.route('/admin/sources/newsapi/update', methods=['POST'])
def update_newsapi():
    newsapi_api = NewsApiApi()
    data = newsapi_api.update_source();
    return jsonify(data);

@app.route('/admin/sources/newsapi/crawl', methods=['POST'])
def crawl_newsapi_fulltext():
    newsapi_api = NewsApiApi()
    data = newsapi_api.crawl_newsapi_fulltext();
    return jsonify(data);

@app.route('/admin/database/articles/remove-fulltext-duplicates', methods=['POST'])
def remove_fulltext_duplicates():
    database_cleaner = DatabaseCleaner()
    data = database_cleaner.article_remove_fulltext_duplicates();
    return jsonify(data);

@app.route('/admin/database/articles/remove-url-duplicates', methods=['POST'])
def remove_url_duplicates():
    database_cleaner = DatabaseCleaner()
    data = database_cleaner.article_remove_url_duplicates();
    return jsonify(data);

@app.route('/admin/database/articles/populate-source', methods=['POST'])
def populate_source_from_articles():
    database_cleaner = DatabaseCleaner()
    data = database_cleaner.populate_source_from_articles();
    return jsonify(data);


