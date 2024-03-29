import collections
import threading
import feedparser
import time
from datetime import datetime, timedelta
import pytz

Post = collections.namedtuple('Post', [
    'time',
    'blog',
    'title',
    'author',
    'body'
])


class FeedparserThread(threading.Thread):
    def __init__(self,feedUrl,feedStart,allPosts):
        threading.Thread.__init__(self)
        self.feedUrl = feedUrl
        self.feedStart = feedStart
        self.AllPosts = allPosts

    def run(self):
        feed = feedparser.parse(self.feedUrl)
        feedPosts = []
        blog = feed['feed'].get('title','No Title')
        sourceTZ = pytz.timezone('UTC')
        destTZ = pytz.timezone('America/Chicago')
        feedTime = self.feedStart.replace(tzinfo=destTZ).astimezone(destTZ)
        for entry in feed['entries']:
            postTime = entry.get('updated_parsed',0)
            if not postTime:
                postTime = entry.get('published_parsed',0)
            UTCTime = pytz.utc.localize(datetime.fromtimestamp(time.mktime(postTime)))
            # Converting TZ
            #UTCTime.replace(tzinfo=sourceTZ)
            entryTime = UTCTime.astimezone(destTZ)
            if entryTime > feedTime:
                # pulling only fresh entries
                post = self.parseEntry(entry, blog, entryTime)
                if post:
                    feedPosts.append(post)
        feedPosts.sort()
        self.AllPosts += feedPosts 

    def parseEntry(self, entry, blog, entryTime):
        title = entry.get('title', "No Title")
        author = entry.get('author',blog)
        try:
            body = entry['content'][0]['value']
        except KeyError:
            body = entry.get('summary','No Information')
        return Post(entryTime, blog, title, author, body)
        
