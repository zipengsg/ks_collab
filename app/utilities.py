from sqlalchemy import and_, or_
from app import db
from app.models import Article

# pylint: disable=no-member
# pylint: disable=singleton-comparison
# pylint: disable=no-self-use

class DatabaseCleaner():
    """
    DatabaseCleaner class contains various functions that standardize data within different tables.
    While care is taken during data collection and initial database population stage,
        certain bad data may still be introduced.
    """
    def article_remove_fulltext_duplicates(self):
        """
        article_remove_fulltext_duplicates identifies duplicates within fulltext of entries in the
            Article table. Note that despite coming from different URLs, it may be possible that
            fulltext are exact duplicates of one another.
        article_remove_fulltext_duplicates can also find identical anti-crawl messages from websites
            such as bloomberg and remove those entries.
        """
        articles_all = Article.query.filter(Article.article_fulltext != None).all()
        remove_counter = 0
        for article in articles_all:
            article_fulltext = article.article_fulltext
            duplicate_articles = Article.query.filter(Article.article_fulltext == article_fulltext).all()
            if len(duplicate_articles) > 1:
                # ref_article = duplicate_articles[0]
                for i in range(1, len(duplicate_articles)):
                    print(duplicate_articles[i].article_fulltext)
                    db.session.delete(duplicate_articles[i])
                    remove_counter = remove_counter + 1
        db.session.commit()
        print('removed '+ str(remove_counter) + ' duplicate fulltext rows')
    
    def article_remove_url_duplicates(self):
        """
        article_remove_url_duplicates identifies duplicates within article_url of entries in the
            Article table.
        """
        articles_all = Article.query.filter(and_(Article.article_url != None, Article.article_url != '')).all()
        remove_counter = 0
        for article in articles_all:
            article_url = article.article_url
            duplicate_articles = Article.query.filter(Article.article_url == article_url).all()
            if len(duplicate_articles) > 1:
                # ref_article = duplicate_articles[0]
                for i in range(1, len(duplicate_articles)):
                    print(duplicate_articles[i].article_url)
                    db.session.delete(duplicate_articles[i])
                    remove_counter = remove_counter + 1
        db.session.commit()
        print('removed ' + str(remove_counter) + ' duplicate url rows')