#!/usr/bin/env python3

import json
import os.path
import logging

from configparser import ConfigParser
from news import MyNews

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
        exit(1)

# parse config file
newsConfig = ConfigParser()
newsConfig.read(configFile)


# launch service
newsService = MyNews(newsConfig = newsConfig)
while True:
    newsService.precheck()
    newsService.getNews()
    newsService.buildFile()
    newsService.compileBook()
    newsService.updatePullDate()
    newsConfig.set('news','newsLastPull',newsService.startTime.strftime("%Y-%m-%d %H:%M:%S.%f"))
    with open(configFile,"w") as handler:
        newsConfig.write(handler)
    newsService.sleep()
