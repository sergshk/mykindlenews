import collections
import threading
import feedparser
import time
from datetime import datetime, timedelta

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
        for entry in feed['entries']:
            postTime = entry.get('updated_parsed',0)
            if not postTime:
                postTime = entry.get('published_parsed',0)
            entryTime = datetime.fromtimestamp(time.mktime(postTime))
            feedTime = self.feedStart
            if entryTime > self.feedStart:
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
        
