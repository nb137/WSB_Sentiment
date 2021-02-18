# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 15:16:16 2021

Resources:
    https://www.storybench.org/how-to-scrape-reddit-with-python/
    https://www.learndatasci.com/tutorials/sentiment-analysis-reddit-headlines-pythons-nltk/
    https://towardsdatascience.com/how-to-get-free-historical-and-live-stock-prices-and-fx-rates-using-python-part-i-a7718f0a4e4

@author: nb137
"""

import praw
import pandas as pd
import datetime
import yfinance as yf
from praw.models import MoreComments

# GME, TSLA, PLTR, others 
ticker = "GME"
text = "Game Stop"

# Hiding my API keys and such in this py file that is not in the public repo
# See this for a how-to: https://www.storybench.org/how-to-scrape-reddit-with-python/
from api_help import reddit # returns a reddit object from praw
    
subreddit = reddit.subreddit('wallstreetbets')



# # Thoughts on progress:
# Pick a couple meme stocks
# Look at both daily thread and top posts in general with search
# Sentiment and number of posts vs. price

stck = yf.Ticker(ticker)
#stck.info
hist = stck.history(period="30d")
hist.index = hist.index.tz_localize('US/Pacific')
# TODO: build plot for daily min, max, volume

#d = subreddit.search("Daily Discussion Thread", sort="new", syntax='lucene', time_filter='month')
# Next line is easier, search by flair and don't have to filter out after
d = subreddit.search('flair:"Daily Discussion"', sort="new", syntax='lucene', time_filter='month')
# note i see no difference in syntax between lucene and cloudsearch
daily_comments = pd.DataFrame()
all_com = pd.DataFrame()
ids, titles,epoch = [],[],[]
for daily_thread in d:
    if daily_thread.num_comments == 0:
        # Some threads re-created or nuked? Skip if no comments
        continue
    titles.append(daily_thread.title)
    ids.append(daily_thread.id)
    epoch.append(daily_thread.created_utc)
    all_top_level_comments,tlc_score,tlc_epoch = [],[],[]
    #Analyze all(?) top-level comments of daily thread
    for top_level_comment in daily_thread.comments:   
        if isinstance(top_level_comment, MoreComments):
            continue    # Skip instances of more comments
        all_top_level_comments.append(top_level_comment.body)
        tlc_score.append(top_level_comment.score)
        tlc_epoch.append(top_level_comment.created_utc)
    daily_df = pd.DataFrame({'tl_comment':all_top_level_comments,'tl_com_score':tlc_score,'tl_com_epoch':tlc_epoch})
    daily_df['parent_id'] = daily_thread.id
    daily_df['parent_epoch'] = daily_thread.created_utc
    
    all_com = pd.concat([all_com,daily_df],axis=0,ignore_index=True)
    # Do ticker/name search here to reduce number of lines
    daily_df = daily_df[daily_df['tl_comment'].str.contains(ticker+"|"+text,case=False,regex=True)]
    
    daily_comments = pd.concat([daily_comments,daily_df],axis=0,ignore_index=True)

# For each line, can do sentiment analysis (see Sentiment Analysis file)
all_com['com_dt'] = pd.to_datetime(all_com['tl_com_epoch'],unit='s', utc=True).dt.tz_convert('US/Pacific')
all_com['parent_dt'] = pd.to_datetime(all_com['parent_epoch'],unit='s', utc=True).dt.tz_convert('US/Pacific')

daily_comments['com_dt'] = pd.to_datetime(daily_comments['tl_com_epoch'],unit='s', utc=True).dt.tz_convert('US/Pacific')
daily_comments['parent_dt'] = pd.to_datetime(daily_comments['parent_epoch'],unit='s', utc=True).dt.tz_convert('US/Pacific')

# Number of posts per day on stock ticker
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
grouped = daily_comments.resample('D', on='com_dt')['tl_comment'].count()

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twinx()
hist.Volume.plot(kind='bar', ax=ax1,color='red', position=0, label='Stock Volume')
grouped.plot(kind='bar',ax=ax2,color='blue',position=1, label='WSB daily comments')
ax1.set_title(ticker+" Volume vs WSB Comments")
fig.legend()
ax1.set_title(ticker+" Volume vs WSB Comments")
ax1.set_ylabel('Volume')
ax2.set_ylabel('WSB Daily Comments')
locs,labels = plt.xticks()
plt.xticks(locs,[pd.to_datetime(i.get_text()).strftime('%m-%d-%y')  for i in labels],rotation=20)
ax1.tick_params(rotation=30)

# TODO Add candlestick chart for stock?
# TODO Add standalone threads with stock name in it?