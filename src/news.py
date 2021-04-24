import json
import logging
import os
import subprocess
import time
# pypandoc is the only part of real docker environment, we can skip for testing
try:
    import pypandoc
except ImportError:
    logging.info("Error initializing pypandoc and it's skipped")

from parser import FeedparserThread
from datetime import datetime, timedelta


class MyNews():
    # TODO move templates into a separate class
    templateHeader = u"""<html>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width" />
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
      <meta name="apple-mobile-web-app-capable" content="yes" />
    <style>
    </style>
    <title>MY DAILY NEWS {today}</title>
    </head>
    <body>
    
    """
    templateFooter = u"""
    </body>
    </html>
    """
    templateSinglePost = u"""
        <article>
            <h1>::: {title}</h1>
            <p><small>By {author} for <i>{blog}</i>, <b>on {postdate}</b>.</small></p>
             {body}
        </article>
    """

    def __init__(self, newsConfig):
        self.newsFeeds = json.loads(newsConfig.get('news','newsFeeds'))
        self.newsFrequency = newsConfig.get('news','newsFrequency')
        lastPullString = newsConfig.get('news','newsLastPull', fallback='')
        if not lastPullString:
            self.startTime = datetime.now() - timedelta(hours=int(self.newsFrequency))
        else:
            self.startTime = datetime.strptime(lastPullString, "%Y-%m-%d %H:%M:%S.%f")
        self.pandocPath = newsConfig.get('osENV','pandocPath')
        self.outputFolder = newsConfig.get('osENV','outputFolder')
    
    def getPosts(self):
        """
        Method to pull all news and organize them into array
        """
        # TODO do we really need threading here or it can just do fine without
        allPosts = []
        threads = []
        feedTime = self.startTime
        for oneUrl in self.newsFeeds:
            thread = FeedparserThread(oneUrl, self.startTime, allPosts)
            threads.append(thread)
            thread.start()

        # Joining all threads into one
        for thread in threads:
            thread.join()

        return allPosts

    def getNews(self):
        logging.info("Getting news")
        self.newsPosts = self.getPosts()

    def buildFile(self):
        # We are building HTML file
        logging.info("Generating HTML")
        self.newsHTML=""
        if self.newsPosts:
            self.newsHTML = self.templateHeader.format(today=self.startTime.strftime('%d %B %Y').strip('0'))
            for singlePost in self.newsPosts:
                postDict = singlePost._asdict()
                if len(postDict['body']) > 300:
                    postDict['postdate'] = postDict['time'].strftime('%d %B %Y').strip('0')
                    self.newsHTML += u"\n"+self.templateSinglePost.format(**postDict)
                else:
                    logging.info("Discarding post"+postDict['title'])
            self.newsHTML += self.templateFooter

    def compileBook(self, debugMode=False):
        # We are compiling book here
        logging.info("Building epub")
        if debugMode:
            htmlFile = os.path.join(self.outputFolder,'dailynews_'+self.startTime.strftime('%Y_%m_%d')+'.html')
            htmlHandler = open(htmlFile,"w")
            htmlHandler.write(self.newsHTML)
            htmlHandler.close()
            return
        epubFile = os.path.join(self.outputFolder,'dailynews.epub')
        mobiFile = os.path.join(self.outputFolder,'dailynews_'+self.startTime.strftime('%Y_%m_%d')+'.mobi')

        # TODO there is gotta be more elegant way to pass this variable 
        # we can move it to Docker
        os.environ['PYPANDOC_PANDOC'] = self.pandocPath 
        pypandoc.convert_text(self.newsHTML,to='epub3',format="html",outputfile=epubFile,extra_args=["--standalone", ])
        logging.info("Converting to mobi")
        cmd = ['ebook-convert', epubFile, mobiFile]
        process = subprocess.Popen(cmd)
        process.wait()

        logging.info("Cleaning up...")
        os.remove(epubFile)

    def updatePullDate(self):
        """
        Method that updates startTime to now, as we just included all news 
        """
        self.startTime = datetime.now() 

    def sleep(self):
        """
        Method that ensures news are generated in accordance with a frequency 
        """
        # Just spending cycles of sleep till next date
        timeTarget = self.startTime + timedelta(hours=int(self.newsFrequency))
        while datetime.now() < timeTarget:
            # sleep for 30 min
            # TODO move time to sleep into config
            logging.info(f"Sleep for 30 min target to wakeup {timeTarget}")
            time.sleep(60*30)

    def precheck(self):
        """
        Method that ensures container continue to sleep until time to pull more news, in case container was restarted
        """
        # making sure it's a time for pull, otherwise just sleep
        if datetime.now() < self.startTime + timedelta(hours=int(self.newsFrequency)):
            logging.info("Didn't reach time to wakeup yet, going to sleep")
            self.sleep()
