from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os
import logging

# TODO replace this hack
serverPath = ""

class ServerHandler(BaseHTTPRequestHandler):
    templateHeader = u"""<html>
    <head>
    <title> My Daily News</title>
    <meta charset="UTF-8" />
    </head>
    <body>
    <h1>Available News</h1>
    """
    templateFile = u"""
    <p><a href="{fileName}">{fileTitle}</a></p>
    """
    templateFooter = u"""
    </body>
    </html>
    """

    def do_GET(self):
        global serverPath
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(self.templateHeader,"utf-8"))
            for singleFile in os.listdir(serverPath):
                if os.path.isfile(os.path.join(serverPath,singleFile)):
                    # Removing index.html from newslisting
                    if "index.html" != singleFile:
                        fileParts = singleFile.split(".")
                        self.wfile.write(bytes(self.templateFile.format(fileName = singleFile, fileTitle = fileParts[0].upper()),"utf-8"))
            self.wfile.write(bytes(self.templateFooter,"utf-8"))
        else:
            localName = os.path.join(serverPath,self.path.strip("/").strip("."))
            logging.info(f"Requested path {localName}")
            if os.path.exists(localName) and os.path.isfile(localName):
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.end_headers()
                with open(localName, "rb") as bfile:
                    binData = bfile.read()
                self.wfile.write(binData)
            else:
                self.send_response(404)


class ServerThread(threading.Thread):
    def __init__(self,newsConfig):
        global serverPath 
        threading.Thread.__init__(self)
        self.hostName = newsConfig.get('server','hostName', fallback='localhost')
        self.serverPort = newsConfig.get('server','serverPort', fallback='8080')
        serverPath = newsConfig.get('osENV','outputFolder')
        globalVar = "Test2"

    def run(self):
        logging.info(f"Starting webserver {self.hostName} on port {self.serverPort}")
        webServer = HTTPServer(("", int(self.serverPort)), ServerHandler)
        webServer.serve_forever()
