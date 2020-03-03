from tweepy import API
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

from textblob import TextBlob

import twitter_credentials
import numpy as np
import pandas as pd
import re
import matplotlib.pyplot as plt

#### Twitter Client ####
class TwitterClient():
    # Default twitter user is None. If none provided, it will go to your own timeline
    def __init__(self, twitter_user=None):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)
        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client
    
    def get_user_timeline_tweets(self, num_tweets):
        tweets = []
        # Loop through every tweet cursor object provides
        # if user_timeline is not provided (default param), it will go into your own timeline
        # num_tweets = num of tweets to get
        for tweet in Cursor(self.twitter_client.user_timeline, id=self.twitter_user).items(num_tweets):
            tweets.append(tweet)
        return tweets

    def get_friend_list(self, num_friends):
        friend_list = []
        # Looping through user's timeline, get certain number of user's friends
        for friend in Cursor(self.twitter_client.friends, id=self.twitter_user).items(num_friends):
            friend_list.append(friend)
        return friend_list
    
    def get_home_timeline_tweets(self, num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(self.twitter_client.home_timeline_tweets, id=self.twitter_user).items(num_tweets):
            home_timeline_tweets.append(tweet)
        return home_timeline_tweets

#### Twitter Authenticator ####
class TwitterAuthenticator():

    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth

#### Twitter Streamer ####
class TwitterStreamer():
    """
    Class for streaming and processing live tweets
    """

    def __init__(self):
        self.twitter_authenticator = TwitterAuthenticator()

    def stream_tweets(self, fetched_tweets_file, hash_tag_list):
        # Handles Twitter authentication and connection to Twitter streaming API
        listener = TwitterListener(fetched_tweets_file)
        auth = self.twitter_authenticator.authenticate_twitter_app()
        stream = Stream(auth, listener)

        # Filter tweets based on list of keywords
        # Takes a list (named track)
        # If tweet contains one of these list objects, it will be added to the stream
        stream.filter(track=hash_tag_list)

#### Twitter Listener ####
class TwitterListener(StreamListener):
    """
    Basic listener class that prints received tweets to stdout
    """

    def __init__(self, fetched_tweets_file):
        self.fetched_tweets_file = fetched_tweets_file

    # Take in data streamed in from StreamListener
    def on_data(self, data):
        try:
            print(data)
            with open(self.fetched_tweets_file, 'a') as tf:
                tf.write(data)
            return True
        except BaseException as e:
            print("Error on_data: %s" % str(e))
        return True

    # Overriding StreamListener class in case an error occurs. Prints status message
    def on_error(self, status):
        if status == 420:
            # returning false on_data method in case rate limit occurs
            return False
        print(status)

#### Tweet Analyzer ###
class TweetAnalyzer():
    """
    Functionality for analyzing and catagorizing contents from tweets
    """

    # Sanitize tweets
    def clean_tweet(self, tweet):
        # Removing special chars and hyperlinks from tweet
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyze_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))

        if analysis.sentiment.polarity > 0:
            # return 1 for positive
            return 1
        elif analysis.sentiment.polarity == 0:
            # neutral
            return 0
        else: 
            # negative
            return -1

    # Convert JSON format tweet to data frame
    def tweets_to_data_frame(self, tweets):
        # Extract text from each of the tweets
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['tweets'])
        
        # Creating column in dataframe named id
        df['id'] = np.array([tweet.id for tweet in tweets])
        df['len'] = np.array([len(tweet.text) for tweet in tweets])
        df['date'] = np.array([tweet.created_at for tweet in tweets])
        df['source'] = np.array([tweet.source for tweet in tweets])
        df['likes'] = np.array([tweet.favorite_count for tweet in tweets])
        df['retweets'] = np.array([tweet.retweet_count for tweet in tweets])

        return df



if __name__ == "__main__":

    twitter_client = TwitterClient()
    tweet_analyzer = TweetAnalyzer()
    api = twitter_client.get_twitter_client_api()

    # Obtain tweets from client
    # user_timeline is a function provided by twitter client API, not a function we've written (function FROM Twitter client)
    # screen_name = username of twitter user
    # count = num of tweets
    tweets = api.user_timeline(screen_name="WHO", count=100)

    # Creating data frame object
    df = tweet_analyzer.tweets_to_data_frame(tweets)
    # Looping through each tweet in the data frame column corresponding to 'tweets' created above
    df['sentiment'] = np.array([tweet_analyzer.analyze_sentiment(tweet) for tweet in df['tweets']])
    print(df.head(10))

    # Get average length of all tweets
    # print(np.mean(df['len']))

    # Get the number of likes for the most-liked tweet
    # print(np.max(df['likes']))

    # Get the number of retweets for the most retweeted tweet
    # print(np.max(df['retweets']))

    # Time series
    # time_likes = pd.Series(data=df['likes'].values, index=df['date'])
    # time_likes.plot(figsize=(16, 4), label='likes', legend=True)

    # time_retweets = pd.Series(data=df['retweets'].values, index=df['date'])
    # time_retweets.plot(figsize=(16,4), label='retweets', legend=True)
    # plt.show()

