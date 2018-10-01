from sqlalchemy import and_, or_
from app import db
from app.models import Article, Source

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
        article_remove_fulltext_duplicates identifies and removes duplicates within fulltext of
            entries in the Article table. Note that despite coming from different URLs, it may 
            be possible that fulltext are exact duplicates of one another.
        article_remove_fulltext_duplicates treats the article with the earliest publish date as
            original.
        article_remove_fulltext_duplicates can also find identical anti-crawl messages from websites
            such as bloomberg and remove those entries.
        """
        articles_all = Article.query.filter(Article.article_fulltext != None).all()
        remove_counter = 0
        for article in articles_all:
            article_fulltext = article.article_fulltext
            duplicate_articles = Article.query.filter(Article.article_fulltext == article_fulltext). \
                                               order_by(Article.article_publishdate.asc()).all()
            if len(duplicate_articles) > 1:
                # ref_article = duplicate_articles[0]
                for i in range(1, len(duplicate_articles)):
                    print(duplicate_articles[i].article_fulltext)
                    duplicate_articles[i].article_status = 'inactive'
                    remove_counter = remove_counter + 1
        db.session.commit()
        print('marked "inactive" for '+ str(remove_counter) + ' duplicate fulltext rows')
    
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
    
    # Retired function after migrating source_name and source_type to Source table successfully
    # def populate_source_from_articles(self):
    #     """
    #     populate_source_from_articles is a helper function for migrating a portion of
    #         the Article table (source_type, source_name) into a new standalone Source
    #         table, which has a one-to-many relationship with the Article table.
    #     """
    #     articles_all = Article.query.filter(and_(Article.source_type != None, Article.source_name != None)).all()

    #     for article in articles_all:
    #         source_name = article.source_name
    #         source_type = article.source_type
    #         associated_source = Source.query.filter(and_(Source.source_type == source_type,
    #                                                      Source.source_name == source_name)).first()
    #         if associated_source is None:
    #             associated_source = Source(source_type=source_type,
    #                                        source_name=source_name,
    #                                        source_url=None,
    #                                        source_description=None,
    #                                        source_statistics=None)
    #             db.session.add(associated_source)
    #         article.source = associated_source
    #     db.session.commit()
    #     print('populated source table with existing articles')
