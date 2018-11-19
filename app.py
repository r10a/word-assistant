import os
import json
import logging
import gevent
from flask import Flask, request
from flask_sockets import Sockets
from time import sleep

# REDIS_URL = "redis://h:p04a8e4cbdb3e36af2c205959d0c8e94d5105fadb2de41cf2ddf9d305572b8a85@ec2-54-158-0-180.compute-1.amazonaws.com:61719" # os.environ['REDIS_URL']
# REDIS_CHAN = 'word-assistant'

# Create the Flask WSGI application.
app = Flask(__name__)
app.debug = 'DEBUG' in os.environ

sockets = Sockets(app)

# Define an handler for the root URL of our application.
@app.route('/')
def hello():
    return "Hello world flask"

class InputRecords:

    def __init__(self):
        self.clients = list()

    def register(self, client):
        """Register a WebSocket connection for Redis updates."""
        self.clients.append(client)

    def receive_from_ga(self):
        content = request.get_json()
        print("content", content)
        queryResult = content['queryResult']
        command = {
            "queryText": queryResult['queryText'],
            "parameters": queryResult['parameters'],
            "user": 1
        }
        app.logger.info(u'Inserting message: {}'.format(command))
        acks = []
        for client in self.clients:
            try:
                client.send(json.dumps(command))
                acks.append(client.receive())
            except Exception:
                self.clients.remove(client)
        print(acks)
        for a in acks:
            if a == True:
                return "Done"
            else:
                return "Error"

input = InputRecords()

app.add_url_rule('/write', 'write', input.receive_from_ga, methods=['POST'])

@sockets.route('/connect')
def outbox(ws):
    """Sends outgoing chat messages, via `ClientBackend`."""
    input.register(ws)
    # ws.send("Connected")
    while not ws.closed:
        # Context switch while `ChatBackend.start` is running in the background.
        sleep(0.1)

if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()