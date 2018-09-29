from datetime import datetime
from sqlalchemy import and_, or_
from app import db
from app.models import User, Post, Topic, Article, Expert, TermMap

class Database_Cleaner():
    def remove_fulltext_duplicates(self):
        articles_all = Article.query.filter(Article.article_fulltext!=None).all()
        remove_counter = 0
        for article in articles_all:
            article_fulltext = article.article_fulltext
            duplicate_articles = Article.query.filter(Article.article_fulltext==article_fulltext).all()
            if len(duplicate_articles) > 1:
                # ref_article = duplicate_articles[0]
                for i in range(1, len(duplicate_articles)):
                    print(duplicate_articles[i].article_fulltext)
                    db.session.delete(duplicate_articles[i])
                    remove_counter = remove_counter + 1
        db.session.commit()
        print('removed '+ str(remove_counter) + ' duplicate fulltext rows')
    
    def remove_url_duplicates(self):
        articles_all = Article.query.filter(and_(Article.article_url!=None, Article.article_url!='')).all()
        remove_counter = 0
        for article in articles_all:
            article_url = article.article_url
            duplicate_articles = Article.query.filter(Article.article_url==article_url).all()
            if len(duplicate_articles) > 1:
                # ref_article = duplicate_articles[0]
                for i in range(1, len(duplicate_articles)):
                    print(duplicate_articles[i].article_url)
                    db.session.delete(duplicate_articles[i])
                    remove_counter = remove_counter + 1
        db.session.commit()
        print('removed ' + str(remove_counter) + ' duplicate url rows')