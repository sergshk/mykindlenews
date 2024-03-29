#!/usr/bin/env python3

import json
import os.path
import logging

# Setting logging level prior to first use
# TODOsee if there is a better place for that
logging.basicConfig(level=logging.INFO)

from configparser import ConfigParser
from news import MyNews
from webserver import ServerThread

# Defining configuration file name and folder
# pay attention to DEVENV variable that stands for development environment
osDEVENV = bool(os.getenv("DEVENV", ""))
if osDEVENV:
    configFolder = 'config'
else:
    configFolder = '/config'
configFile = 'news.ini'

logging.basicConfig(level=logging.INFO)

# check whether config folder available or not and if not pull from current folder
if not os.path.isdir(configFolder):
    if not os.path.exists(configFile):
        logging.info(f"Config file not found {configFile}!")
        exit(1)
else:
    configFile = os.path.join(configFolder, configFile)
    if not os.path.exists(configFile):
        logging.info(f"Config file not found {configFile}!")
        if not os.path.exists(configFile+".sample"):
            logging.info(f"Config file sample not found {configFile}!")
            exit(1)
        else:
            logging.info(f"Found {configFile}! using sample")
            # copy file from a cample, avoid using straight OS function
            confSample = open(configFile+".sample","r")
            confReal = open(configFile,"w")
            for line in confSample:
                confReal.write(line)
            confSample.close()
            confReal.close()


# parse config file
newsConfig = ConfigParser()
newsConfig.read(configFile)

webServer = ServerThread(newsConfig = newsConfig) 
# TODO implement graceful thread destruction upon keyboard interruption
webServer.start()

# launch service
newsService = MyNews(newsConfig = newsConfig)
while True:
    newsService.precheck()
    newsService.getNews()
    newsService.buildFile()
    newsService.compileBook(debugMode = osDEVENV)
    newsService.updatePullDate()
    newsConfig.set('news','newsLastPull',newsService.startTime.strftime("%Y-%m-%d %H:%M:%S.%f"))
    with open(configFile,"w") as handler:
        newsConfig.write(handler)
    newsService.sleep()
