import hashlib
import json
import logging
import os

from datetime import datetime
from contextlib import suppress
from twitter_scraper import get_tweets
from newsplease.crawler import commoncrawl_crawler as commoncrawl_crawler
from newsplease import NewsPlease
from newsapi import NewsApiClient
from sqlalchemy import and_, or_
from app import db
from app.models import Article, Source

# pylint: disable=no-member
# pylint: disable=singleton-comparison
# pylint: disable=no-self-use

class TwitterScraper():
    """
    TwitterScraper invokes the open-source twitter_scraper package which links to Twitter's 
        frontend API.
    The class contains a list of hard-coded Twitter handles that we wish to extract Tweets from.
    This class is one of the ones used to obtain test data for the MVP.
    https://github.com/kennethreitz/twitter-scraper
    """
    # Sets the maximum number of pages of Tweets to scrape
    # Note that scraper may yield an error if it cannot find the specified number of pages of 
    #   existing Tweets
    max_pages = 5 

    # List of Twitter handles; do not include the @ before the name
    twitter_users = list()
    twitter_users.append("JoeBiden")
    twitter_users.append("BillClinton")
    twitter_users.append("MichelleObama")
    twitter_users.append("Comey")
    twitter_users.append("neiltyson")
    twitter_users.append("RepAdamSchiff")
    twitter_users.append("BillGates")

    def update_source(self, twitter_users=twitter_users, max_pages=max_pages):
        """
        Calling update_source will run the Twitter Scraper and update the database with latest 
            Tweets from hard-coded handles.
        If a new handle is included, obtain all Tweets up to max_pages
        Otherwise, update database with new Tweets since last update

        Currently throws an exception if twitter account is invalid or if there are too few tweets
        May need to make the function more robust
        """
        # Create/recall a marker in the database used to identify last update time
        last_update_article = Article.query.filter_by(article_author='twitter_last_update').first()
        if last_update_article is None:
            print('did not find last_update')
            last_update = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')
            last_update_article = Article(source_type='Social Media',
                                          source_name='Twitter',
                                          article_author='twitter_last_update',
                                          article_publishdate=last_update,
                                          article_wordcount=0,
                                          article_title=None,
                                          article_summary=None,
                                          article_fulltext=None,
                                          article_url=None,
                                          article_status=None)
            db.session.add(last_update_article)
            db.session.commit()
        else:
            print('found last_update')
            last_update = last_update_article.article_publishdate
        
        for user in twitter_users:
            print(user)
            tweets = get_tweets(user, pages=max_pages)
            user_sample_article = Article.query.filter_by(article_author=user).first()
            # if twitter user is already in database, update database with only new tweets 
            #   by that user
            if user_sample_article is not None:
                for tweet in tweets:
                    if tweet['time'] > last_update:
                        wordcount = len(tweet['text'].split(" "))
                        article = Article(source_type='Social Media',
                                          source_name='Twitter',
                                          article_author=user,
                                          article_publishdate=tweet['time'],
                                          article_wordcount=wordcount,
                                          article_title=None,
                                          article_summary=tweet['text'],
                                          article_fulltext=tweet['text'],
                                          article_url=None,
                                          article_status=None)
                        db.session.add(article)
            # if new twitter user to be followed, update database with older tweets as well
            else:
                for tweet in tweets:
                    wordcount = len(tweet['text'].split(" "))
                    article = Article(source_type='Social Media',
                                      source_name='Twitter',
                                      article_author=user,
                                      article_publishdate=tweet['time'],
                                      article_wordcount=wordcount,
                                      article_title=None,
                                      article_summary=tweet['text'],
                                      article_fulltext=tweet['text'],
                                      article_url=None,
                                      article_status=None)
                    db.session.add(article)
        last_update = datetime.utcnow()
        last_update_article.article_publishdate = last_update
        db.session.commit()
        print('twitter source updated!')

class NewsApiApi():
    """
    NewsAPIAPI invokes the open-source newsapi package which is a Python wrapper for NewsAPI's 
        API to download articles.
    NewsAPI requires an API key for all users, and contains restrictions on query specificity 
        and number of articles returned at a time.
    For the "Developers" plan, NewsAPI does not provide fulltext. The open-source newsplease 
        package is used to enrich data obtained through NewsAPI by scraping each site based on URL.
    NewsAPI returns data for each query in json format
    """
    # Unique API key used to make requests from NewsAPI
    api = NewsApiClient(api_key='fa676399ed04400d851b69e911c70921')

    # Directory to store returned json files
    file_dir = './newsapi_download_articles/'

    # Keyword constraint, now defined in front-end StringField
    # my_q = 'oscar' 

    # Chosen list of sources. Note that the following sources have anti-crawl:
    #   bloomberg
    # Find additional source names here: https://newsapi.org/sources
    my_sources = 'abc-news, bbc-news, business-insider, cbs-news, \
                cbs-news, cnn, espn, fox-news, fox-sports, \
                ign, msnbc, national-geographic, politico, rt, \
                techcrunch, the-economist, the-new-york-times, the-wall-street-journal, wired'
    my_domains = None
    my_from = None
    my_to = '2018-09-26' #YYYY-MM-DD
    my_language = 'en'
    my_sort_by = 'relevancy' # publishedAt, popularity, relevancy
    my_page_size = 100 # max page size is 100
    # max_pages = 3 # defined in front-end StringField

    def request_source(self, my_q, max_pages, 
                       file_dir=file_dir,
                       api=api, 
                       my_sources=my_sources,
                       my_domains=my_domains,
                       my_from=my_from,
                       my_to=my_to,
                       my_language=my_language,
                       my_sort_by=my_sort_by,
                       my_page_size=my_page_size):
        """
        request_source makes an API request to NewsAPI based on specified filtering criteria and 
            saves the returned json file to file_dir
        """
        cur_page = 1
        # Since max page size is 100, use something slightly larger than 100 to initialize
        total_results = 105
        while cur_page*my_page_size < total_results and cur_page <= max_pages:
            all_articles = api.get_everything(q=my_q,
                                              sources=my_sources,
                                              domains=my_domains,
                                              from_param=my_from,
                                              to=my_to,
                                              language=my_language,
                                              sort_by=my_sort_by,
                                              page_size=my_page_size,
                                              page=cur_page)

            with open(file_dir+'test_page_'+str(my_q)+'_'+str(cur_page)+'.json', 'w') as outfile:
                json.dump(all_articles, outfile)
            
            cur_page = cur_page + 1
            total_results = all_articles['totalResults']
            print(all_articles['totalResults'])

    def update_source(self, 
                      file_dir=file_dir):
        """
        update_source goes through every file in the directory that stores NewsAPI's output json 
            files and updates the Article table with all available information.
        update_source does not pull fulltext from the json files, since fulltext from NewsAPI 
            is truncated.
        update_source checks the Article table for duplicate URLs before adding a new entry
        """
        n_articles_added = 0
        for filename in os.listdir(file_dir):
            if filename.endswith('.json'):
                with open(file_dir+filename) as json_data:
                    newsapi_object = json.load(json_data)
                newsapi_articles = newsapi_object['articles']
                for element in newsapi_articles:
                    existing_article = Article.query.filter_by(article_url=element['url']).first()
                    if existing_article is None:
                        publishdate = datetime.strptime(element['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                        source_type = 'News'
                        source_name = element['source']['name']
                        associated_source = Source.query.filter(and_(Source.source_type == source_type,
                                                                     Source.source_name == source_name)).first()
                        if associated_source is None:
                            associated_source = Source(source_type=source_type,
                                                       source_name=source_name,
                                                       source_url=None,
                                                       source_description=None,
                                                       source_statistics=None)
                            db.session.add(associated_source)
                        article = Article(source=associated_source,
                                          article_author=element['author'],
                                          article_publishdate=publishdate,
                                          article_wordcount=None,
                                          article_title=element['title'],
                                          article_summary=None,
                                          article_fulltext=None,
                                          article_url=element['url'],
                                          article_status=None)
                        db.session.add(article)
                        n_articles_added = n_articles_added + 1
                # Flush after parsing each json file to ensure no duplicates are added across files
                # Articles within each file assumed to be unique based on NewsAPI's output specifications
                db.session.flush()
        db.session.commit()
        print('newsAPI sources updated. ' + str(n_articles_added) + ' new articles added!')


class NewspleaseScraper():
    """
    NewspleaseScraper invokes the open-source newsplease package which is a generalized 
        scraper for news websites.
    NewspleaseScraper also contains functionality to extract and scrape commoncrawl data 
        (see commoncrawl.org), but it does not work very well.
    https://github.com/fhamborg/news-please
    """
    ############ CONFIG ############
    # download dir for warc files
    my_local_download_dir_warc = './cc_download_warc/'
    # download dir for articles
    my_local_download_dir_article = './cc_download_articles/'
    # hosts (if None or empty list, any host is OK)
    my_filter_valid_hosts = []  # example: ['elrancaguino.cl']
    # start date (if None, any date is OK as start date), as datetime
    my_filter_start_date = datetime(2016, 9 , 1)  # datetime.datetime(2016, 1, 1)
    # end date (if None, any date is OK as end date), as datetime
    my_filter_end_date = datetime(2018, 9, 27)  # datetime.datetime(2016, 12, 31)
    # if date filtering is strict and news-please could not detect the date of an article, 
    #   the article will be discarded
    my_filter_strict_date = True
    # if True, the script checks whether a file has been downloaded already and uses that file 
    #   instead of downloading
    # again. Note that there is no check whether the file has been downloaded completely 
    #   or is valid!
    my_reuse_previously_downloaded_files = True
    # continue after error
    my_continue_after_error = True
    # show the progress of downloading the WARC files
    my_show_download_progress = True
    # log_level
    my_log_level = logging.INFO
    # json export style
    my_json_export_style = 1  # 0 (minimize), 1 (pretty)
    # number of extraction processes
    my_number_of_extraction_processes = 1
    # if True, the WARC file will be deleted after all articles have been extracted from it
    my_delete_warc_after_extraction = False
    # if True, will continue extraction from the latest fully downloaded but not fully extracted 
    #   WARC files and then
    # crawling new WARC files. This assumes that the filter criteria have not been changed since 
    #   the previous run!
    my_continue_process = True
    ############ END CONFIG #########
    
    def crawl_source(self,
                     my_local_download_dir_warc=my_local_download_dir_warc,
                     my_local_download_dir_article=my_local_download_dir_article,
                     my_json_export_style=my_json_export_style,
                     my_filter_valid_hosts=my_filter_valid_hosts,
                     my_filter_start_date=my_filter_start_date,
                     my_filter_end_date=my_filter_end_date,
                     my_filter_strict_date=my_filter_strict_date,
                     my_reuse_previously_downloaded_files=my_reuse_previously_downloaded_files,
                     my_continue_after_error=my_continue_after_error,
                     my_show_download_progress=my_show_download_progress,
                     my_number_of_extraction_processes=my_number_of_extraction_processes,
                     my_log_level=my_log_level,
                     my_delete_warc_after_extraction=my_delete_warc_after_extraction,
                     my_continue_process=my_continue_process):

        """
        crawl_source is a function that downloads, extracts, scrapes and generates json files 
            from the commoncrawl repository
        Code included below is mostly copy-pasted from examples provided by the package developer
        """
        def __get_pretty_filepath(path, article):
            """
            Pretty might be an euphemism, but this function tries to avoid too long filenames, 
                while keeping some structure.
            :param path:
            :param name:
            :return:
            """
            short_filename = hashlib.sha256(article.filename.encode()).hexdigest()
            sub_dir = article.source_domain
            final_path = path + sub_dir + '/'
            if not os.path.exists(final_path):
                os.makedirs(final_path)
            return final_path + short_filename + '.json'
            
        def on_valid_article_extracted(article):
            """
            This function will be invoked for each article that was extracted successfully from the 
                archived data and that satisfies the filter criteria.
            :param article:
            :return:
            """
            # do whatever you need to do with the article (e.g., save it to disk, store it in ElasticSearch, etc.)
            with open(__get_pretty_filepath(my_local_download_dir_article, article), 'w') as outfile:
                if my_json_export_style == 0:
                    json.dump(article.__dict__, outfile, default=str, separators=(',', ':'))
                elif my_json_export_style == 1:
                    json.dump(article.__dict__, outfile, default=str, indent=4, sort_keys=True)
                # ...
        
        if not os.path.exists(my_local_download_dir_article):
            os.makedirs(my_local_download_dir_article)                                
        commoncrawl_crawler.crawl_from_commoncrawl(on_valid_article_extracted,
                                                   valid_hosts=my_filter_valid_hosts,
                                                   start_date=my_filter_start_date,
                                                   end_date=my_filter_end_date,
                                                   strict_date=my_filter_strict_date,
                                                   reuse_previously_downloaded_files=my_reuse_previously_downloaded_files,
                                                   local_download_dir_warc=my_local_download_dir_warc,
                                                   continue_after_error=my_continue_after_error,
                                                   show_download_progress=my_show_download_progress,
                                                   number_of_extraction_processes=my_number_of_extraction_processes,
                                                   log_level=my_log_level,
                                                   delete_warc_after_extraction=my_delete_warc_after_extraction,
                                                   continue_process=my_continue_process)
    
    
    def crawl_newsapi_fulltext(self):
        """
        crawl_newsapi_fulltext enriches existing rows in Article table that do not have 
            fulltext by going to the associated URL, scraping the site, then obtaining the 
            fulltext of the article and saving it to the database
        """
        # For article filtering against None (Null in database), "is" and "is not" does not work
        articles = Article.query.filter(and_(Article.article_url != None,
                                             Article.article_fulltext == None)).all()
        n = 1
        nmax = 1000 # number of articles to be processed at a time
        for article in articles:
            with suppress(Exception):
                newsplease_article = NewsPlease.from_url(article.article_url)
                article.article_fulltext = newsplease_article.text
                article.article_wordcount = len(newsplease_article.text.split(" "))
                print(n)
                print(article.article_url)
                print(newsplease_article.title)
                # print(newsplease_article.text)
                print('-----------------')
            db.session.flush()
            n = n+1
            if n > nmax:
                break
        db.session.commit()
        
