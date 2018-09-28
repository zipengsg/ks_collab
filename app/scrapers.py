from app import db
from app.models import User, Post, Topic, Article, Expert, TermMap
from twitter_scraper import get_tweets
from newsplease.crawler import commoncrawl_crawler as commoncrawl_crawler
from newsplease import NewsPlease
from newsapi import NewsApiClient
from datetime import datetime
from sqlalchemy import and_, or_
from contextlib import suppress
import hashlib
import json
import logging
import os
import re

class Twitter_Scraper():
    
    twitter_users = list()
    twitter_users.append("JoeBiden")
    twitter_users.append("BillClinton")
    twitter_users.append("MichelleObama")
    twitter_users.append("Comey")
    twitter_users.append("neiltyson")
    twitter_users.append("RepAdamSchiff")
    twitter_users.append("BillGates")

    # currently throws an exception if twitter account is invalid or if there are too few tweets
    # may need to make the function more robust
    def update_source(self, twitter_users=twitter_users):
        last_update_article = Article.query.filter_by(article_author='twitter_last_update').first()
        if last_update_article is None:
            print('did not find last_update')
            last_update = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')
            last_update_article = Article(source_type='Social Media', source_name='Twitter', article_author='twitter_last_update', \
                                        article_publishdate=last_update, article_wordcount=0, article_title=None, article_summary=None, \
                                        article_fulltext=None, article_url=None)
            db.session.add(last_update_article)
            db.session.commit()
        else:
            print('found last_update')
            last_update = last_update_article.article_publishdate
        
        for user in twitter_users:
            print(user)
            tweets = get_tweets(user, pages=5)
            user_sample_article = Article.query.filter_by(article_author=user).first()
            # if twitter user is already in database, update database with only new tweets by that user
            if user_sample_article is not None:
                for tweet in tweets:
                    if tweet['time'] > last_update:
                        wordcount = len(tweet['text'].split(" "))
                        article = Article(source_type='Social Media', source_name='Twitter', article_author=user, \
                                            article_publishdate=tweet['time'], article_wordcount=wordcount, article_title=None, \
                                            article_summary=tweet['text'], article_fulltext=tweet['text'], article_url=None)
                        db.session.add(article)
            # if new twitter user to be followed, update database with older tweets as well
            else:
                for tweet in tweets:
                    wordcount = len(tweet['text'].split(" "))
                    article = Article(source_type='Social Media', source_name='Twitter', article_author=user, \
                                        article_publishdate=tweet['time'], article_wordcount=wordcount, article_title=None, \
                                        article_summary=tweet['text'], article_fulltext=tweet['text'], article_url=None)
                    db.session.add(article)
        last_update = datetime.utcnow()
        last_update_article.article_publishdate = last_update
        db.session.commit()
        print('twitter source updated!')

# NewsAPI key: fa676399ed04400d851b69e911c70921
class NewsAPI_API():

    api = NewsApiClient(api_key='fa676399ed04400d851b69e911c70921')

    ############# Config #############
    file_dir = './newsapi_download_articles/'
    # my_q = 'oscar' # defined in front-end stringfield
    # bloomberg has anti-crawl
    my_sources = 'abc-news, bbc-news, business-insider, cbs-news, \
                cbs-news, cnn, espn, fox-news, fox-sports, \
                ign, msnbc, national-geographic, politico, rt, \
                techcrunch, the-economist, the-new-york-times, the-wall-street-journal, wired'
    my_domains = None
    my_from = None
    my_to = '2018-09-26' #YYYY-MM-DD
    my_language = 'en'
    my_sort_by = 'relevancy' #publishedAt, popularity, relevancy
    my_page_size = 100
    # max_pages = 3 # defined in front-end stringfield
    ############# End Config #########

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

        cur_page = 1
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
        for filename in os.listdir(file_dir):
            if(filename.endswith('.json')):
                with open(file_dir+filename) as json_data:
                    newsAPI_object = json.load(json_data)
                newsAPI_articles = newsAPI_object['articles']
                for element in newsAPI_articles:
                    existing_article = Article.query.filter_by(article_url=element['url']).first()
                    if existing_article is None:
                        publishdate = datetime.strptime(element['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                        article = Article(source_type='News', source_name=element['source']['name'], article_author=element['author'], \
                                            article_publishdate=publishdate, article_wordcount=None, article_title=element['title'], \
                                            article_summary=None, article_fulltext=None, article_url=element['url'])
                        db.session.add(article)
        db.session.commit()
        print('newsAPI sources updated!')

        



#============================================= BELOW DOES NOT WORK PROPERLY ====================================================
class Newsplease_Scraper():

    ############ CONFIG ############
    # download dir for warc files
    my_local_download_dir_warc = './cc_download_warc/'
    # download dir for articles
    my_local_download_dir_article = './cc_download_articles/'
    # hosts (if None or empty list, any host is OK)
    my_filter_valid_hosts = []  # example: ['elrancaguino.cl']
    # start date (if None, any date is OK as start date), as datetime
    my_filter_start_date = datetime(2016, 9 ,1)  # datetime.datetime(2016, 1, 1)
    # end date (if None, any date is OK as end date), as datetime
    my_filter_end_date = datetime(2018, 9, 27)  # datetime.datetime(2016, 12, 31)
    # if date filtering is strict and news-please could not detect the date of an article, the article will be discarded
    my_filter_strict_date = True
    # if True, the script checks whether a file has been downloaded already and uses that file instead of downloading
    # again. Note that there is no check whether the file has been downloaded completely or is valid!
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
    # if True, will continue extraction from the latest fully downloaded but not fully extracted WARC files and then
    # crawling new WARC files. This assumes that the filter criteria have not been changed since the previous run!
    my_continue_process = True
    ############ END CONFIG #########
    
    def crawl_source(self, my_local_download_dir_warc=my_local_download_dir_warc,
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

        def __get_pretty_filepath(path, article):
            """
            Pretty might be an euphemism, but this function tries to avoid too long filenames, while keeping some structure.
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
            This function will be invoked for each article that was extracted successfully from the archived data and that
            satisfies the filter criteria.
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
    
    
    def crawl_newsAPI_fulltext(self):
        articles = Article.query.filter(and_(Article.article_url!=None,Article.article_fulltext==None)).all()
        n = 1
        nmax = 4000
        for article in articles:
            with suppress(Exception):
                newsplease_article = NewsPlease.from_url(article.article_url)
                article.article_fulltext = newsplease_article.text
                article.article_wordcount = len(newsplease_article.text.split(" "))
                print(n)
                print(article.article_url)
                print(newsplease_article.title)
                print(newsplease_article.text)
                print('-----------------')
            db.session.flush()
            n = n+1
            if n > nmax:
                break
        db.session.commit()
        
