# Kaleidoscope developer server setup instructions:

## Preface

This guide assumes basic knowledge of python, and that the developer has python 3 installed on his/her operating system.

Download from github all the files under ks_collab, save it under some high-level directory.

Download `app.db` from email and save it to the same high-level directory.

Navigate to the high-level directory (before entering the "app" folder).

## Setting up the virtual environment

Create virtual environment using the following command:
```
$ python3 -m venv venv
```

Activate virtual environment using the following command:
```
(linux) $ source venv/bin/activate
(windows) $ venv\Scripts\activate
```

## Install Python 3 and all dependencies within the virtual environment
```
flask
flask-sqlalchemy
flask-migrate
flask-wtf
wtforms
python-dotenv
twitter-scraper
news-please
awscli
newsapi-python
pylint
...
(more to be added)
```

## Set `FLASK_APP` environment variable
```
(linux) $ export FLASK_APP=microblog.py
(windows) $ set FLASK_APP=microblog.py
```

## Run the server
```
$ flask run
```
Go to [http://localhost:5000/test](http://localhost:5000/test) to access the admin interface

## 5. Update the admin interface as needed to conduct unit testing

Relevant files to update frontend UI:
```
routes.py
forms.py
templates/test.html
```

Alternatively use console to test without running the server.

