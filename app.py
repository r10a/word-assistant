import os
import json
import logging
import gevent
from flask import Flask, request, jsonify
from flask_sockets import Sockets
from time import sleep

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
            if not client.closed:
                try:
                    client.send(json.dumps(command))
                    acks.append(client.receive())
                except Exception:
                    self.clients.remove(client)
        print(acks)
        response = ""
        for a in acks:
            if a == True:
                response = "Done. Please continue"
                break
            else:
                response = "Sorry. Somthing went wrong. Please try again."

        return jsonify({
            "payload": {
                "google": {
                    "expectUserResponse": true,
                    "richResponse": {
                        "items": [
                            {
                                "simpleResponse": {
                                    "textToSpeech": "Sorry. Somthing went wrong. Please try again."
                                }
                            }
                        ]
                    }
                }
            }
        })


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
