import requests
import os


def requestServer(serverURL, thisMessage, thisContent):
    url = serverURL, 
    myobj = {'message': thisMessage, "content": thisContent}

    x = requests.post(serverURL, json = myobj)

    print(x.json())

requestServer('http://localhost:9500', "process asmr file", os.path.abspath("short.mp3"))