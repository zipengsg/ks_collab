from app import db
from app.models import User, Post, Topic, Article, Expert, TermMap
from twitter_scraper import get_tweets
from newsplease.crawler import commoncrawl_crawler as commoncrawl_crawler
from datetime import datetime
import hashlib
import json
import logging
import os

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
                                        article_publishdate=last_update, article_wordcount=0, article_summary='', \
                                        article_fulltext='', article_url='')
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
                                            article_publishdate=tweet['time'], article_wordcount=wordcount, article_summary=tweet['text'], \
                                            article_fulltext=tweet['text'], article_url='')
                        db.session.add(article)
            # if new twitter user to be followed, update database with older tweets as well
            else:
                for tweet in tweets:
                    wordcount = len(tweet['text'].split(" "))
                    article = Article(source_type='Social Media', source_name='Twitter', article_author=user, \
                                        article_publishdate=tweet['time'], article_wordcount=wordcount, article_summary=tweet['text'], \
                                        article_fulltext=tweet['text'], article_url='')
                    db.session.add(article)
        last_update = datetime.utcnow()
        last_update_article.article_publishdate = last_update
        db.session.commit()
        print('twitter source updated!')
        
class Commoncrawl_Scraper():

    ############ CONFIG ############
    # download dir for warc files
    my_local_download_dir_warc = './cc_download_warc/'
    # download dir for articles
    my_local_download_dir_article = './cc_download_articles/'
    # hosts (if None or empty list, any host is OK)
    my_filter_valid_hosts = []  # example: ['elrancaguino.cl']
    # start date (if None, any date is OK as start date), as datetime
    my_filter_start_date = datetime(2017,12 ,1)  # datetime.datetime(2016, 1, 1)
    # end date (if None, any date is OK as end date), as datetime
    my_filter_end_date = datetime(2018, 1, 31)  # datetime.datetime(2016, 12, 31)
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
    my_delete_warc_after_extraction = True
    # if True, will continue extraction from the latest fully downloaded but not fully extracted WARC files and then
    # crawling new WARC files. This assumes that the filter criteria have not been changed since the previous run!
    my_continue_process = True
    ############ END CONFIG #########
    
    def crawl_source(self, my_filter_valid_hosts=my_filter_valid_hosts,
        my_filter_start_date=my_filter_start_date,
        my_filter_end_date=my_filter_end_date,
        my_filter_strict_date=my_filter_strict_date,
        my_reuse_previously_downloaded_files=my_reuse_previously_downloaded_files,
        my_local_download_dir_warc=my_local_download_dir_warc,
        my_continue_after_error=my_continue_after_error,
        my_show_download_progress=my_show_download_progress,
        my_number_of_extraction_processes=my_number_of_extraction_processes,
        my_log_level=my_log_level,
        my_delete_warc_after_extraction=my_delete_warc_after_extraction,
        my_continue_process=my_continue_process):

        def on_valid_article_extracted(article):
            print(article.title)
            print(article.source_domain)
                                                
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
    
    def update_source(self):
        print()
