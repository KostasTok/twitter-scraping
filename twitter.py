import os
import time
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

def sec_to_str(sec):
    '''
    Gets int 'sec' and returns str with corresponding
    time in hours, min, sec.
    '''
    sec = int(sec)
    hours = sec // 3600
    sec   = sec %  3600
    minut = sec // 60
    sec   = sec %  60
    if hours != 0:
        return 'Duration: {} hours, {} mins, {} secs'.format(hours, minut, sec)
    elif minut != 0:
        return 'Duration: {} mins, {} secs'.format(minut, sec)
    else:
        return 'Duration: {} secs'.format(sec)

def get_account_tweets(username, max_tweets=None, report_time=2):
    '''
    Inputs:
    username -> str with name of account. For example, to work with
            https://mobile.twitter.com/barackobama give barackobama
    max_tweets -> maximum number of tweets to extract. None extracts all.
    report_time -> secs between each report on the process
    
    Loads the legacy version of twitter (without javascript). Each page of
    this version has approximately 20 tweets. The algorithm extracts them
    and click on the 'Load older Tweets' button to move on to next page.
    
    Returns: dataframe with the extracted tweets
    '''
    
    # Get url of 1st page of the account
    url = 'https://mobile.twitter.com/' + username
    
    # Get stats of this account
    r = requests.get(url=url)
    rb = BeautifulSoup(r.text, 'html.parser')
    profile = rb.body.find(id='container').find(id='main_content').find('div','profile')
    stats = profile.find('table','profile-stats').find_all('td','stat')
    tweets_count = int(stats[0].find('div', 'statnum').get_text().replace(',',''))
    following_count = int(stats[1].find('div', 'statnum').get_text().replace(',',''))
    followers_count = int(stats[2].find('div', 'statnum').get_text().replace(',',''))
    
    # Adjust number of max_tweets
    if max_tweets is None:
        max_tweets = tweets_count
    else:
        max_tweets = min(max_tweets, tweets_count)
        
    # Create empty dataframe and set 'i' to zero as its index
    df = pd.DataFrame(
        index=range(max_tweets),
        columns=['username','fullname','href','timestamp','data-id','text'])
    i  = 0
    
    # Each loop adds the tweets extracted from url and gives back url
    # of next page if available. Otherwise url is None and process stops
    first_time = time.time()
    last_time  = first_time
    while (i < max_tweets) and (url is not None):
        df, url, i = extract_tweets_from_account_page(df, url, i)
        # Generate report
        if time.time()-last_time > report_time:
            rep1 = '\rProcess: {:3.2f}%, '.format(100*i/max_tweets)
            rep2 = sec_to_str(time.time()-first_time) 
            print(rep1+' '+rep2 , end='')
            last_time = time.time()
    print('Process: 100% ' + rep2, end='')    
    
    return df, [tweets_count, following_count, followers_count]
    
def get_page_tweets(df, url, i):
    '''
    Used by 'get_account_tweets' to get the tweets from a single
    page (each page of an account holds aprox 20 tweets).
    
    If there is button with the link of the next page with tweets
    of this account, then it also returns that
    '''
    
    got_tweets = False
    while not got_tweets:
        try:
            # Download html
            r = requests.get(url=url)
            rb = BeautifulSoup(r.text, 'html.parser')
            # Get list of tweets
            main = rb.body.find(id='container').find(id='main_content')
            tweets = main.find('div','timeline').find_all('table','tweet')
            got_tweets = True
        except:
            # Some times twitter requires a small break (2 sec approx)
            # before responding to new requests
            time.sleep(0.5)
            print('waiting on: '+url)
    
    # Extract info from each tweet on page
    for tweet in tweets:
        href = tweet.get('href')
        df.loc[i,'href'] = href
        df.loc[i,'username'] = href[1:href.find('/',1)]
        df.loc[i,'fullname'] = tweet.find('tr', 'tweet-header').find_all('a')[1].strong.text
        df.loc[i,'timestamp'] = tweet.find('tr', 'tweet-header').find('td', 'timestamp').text
        df.loc[i,'data-id'] = tweet.find('tr', 'tweet-container').find('div', 'tweet-text').get('data-id')
        df.loc[i,'text'] = tweet.find('tr', 'tweet-container').find('div', 'dir-ltr').text
        i += 1
        
    try: # Get url of next page
        href = main.find('div','timeline').find('div', 'w-button-more').find('a').get('href')
        url = 'https://mobile.twitter.com' + href
    except: # if twitter doesn't give next button
        url = None 
    
    return df, url, i

def get_following(username, max_following=None, report_time=2):
    '''
    Inputs:
    username -> str with name of account. For example, to work with
            https://mobile.twitter.com/barackobama give barackobama
    max_tweets -> maximum number of following to extract. None extracts all.
    report -> True, to get a report on the extraction while it is running
    
    Loads the legacy version of twitter (without javascript). Each page of
    this version has approximately 20 entries. The algorithm extracts them
    and click on the 'Show more people' button to move on to next page.
    
    Returns: dataframe with the full names and user names of the account
    that the 'username' is following
    '''
    
    url = 'https://mobile.twitter.com/' + username + '/following'
    
     # Get total count of following
    r = requests.get(url=url)
    rb = BeautifulSoup(r.text, 'html.parser')
    profile = rb.body.find(id='container').find(id='main_content').find('div','profile')
    count   = profile.find('div','user-header').find_all('td','info')[1].find('span').get_text()
    count   = int(count.replace(',',''))
    # Adjust number of max_following
    if max_following is None:
        max_following = count
    else:
        max_following = min(count, max_following)
        
    following = pd.DataFrame(index=range(max_following),
                             columns={'username', 'fullname'})
    i = 0
        
    # Each loop adds the tweets extracted from url and gives back url
    # of next page if available. Otherwise url is None and process stops
    first_time = time.time()
    last_time  = first_time
    while (i < max_following) and (url is not None):
        following, url, i = get_following_page(following, url, i)
        # Generate report
        if time.time()-last_time > report_time:
            rep1 = '\rProcess: {:3.2f}%, '.format(100*i/max_following)
            rep2 = sec_to_str(time.time()-first_time) 
            print(rep1+' '+rep2 , end='')
            last_time = time.time()
    print('Process: 100%, ' + rep2, end='') 
        
    return following

def get_following_page(following, url, i):
    '''
    Used by 'get_following' to get the accounts from a single
    page (each page of an account holds aprox 20 tweets).
    
    If there is button with the link of the next page with tweets
    of this account, then it also returns that
    '''
    
    got_items = False
    while not got_items:
        try:
            # Download html
            r = requests.get(url=url)
            rb = BeautifulSoup(r.text, 'html.parser')
            profile = rb.body.find(id='container').find(id='main_content').find('div','profile')
            user_items = profile.find('div','user-list').find_all('table','user-item')
            got_items = True
        except:
            # Some times twitter requires a small break (2 sec approx)
            # before responding to new requests
            time.sleep(0.5)
            print('waiting on: ' + url)
    
    for item in user_items:
        a = item.find('td', 'info fifty screenname').find_all('a')
        following.loc[i, 'username'] = a[0].get('name')
        following.loc[i, 'fullname'] = a[1].find('strong').get_text()
        i += 1
    
    try: # get url of next page
        href = profile.find('div','w-button-more').find('a').get('href')
        url = 'https://mobile.twitter.com' + href
    except: # except twitter does not give button for next page
        url = None
        
    return following, url, i