"""`main` is the top level module for your Bottle application."""

# import the Bottle framework
from bottle import request, Bottle, abort, get
# from bottle.ext.websocket import GeventWebSocketServer
# from bottle.ext.websocket import websocket
# from gevent.pywsgi import WSGIServer
import os
import json


import logging
from bottle import ServerAdapter
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket.logging import create_logger

class GeventWebSocketServer(ServerAdapter):

    def run(self, handler):
        server = pywsgi.WSGIServer((self.host, self.port), handler, handler_class=WebSocketHandler, **self.options)

        if not self.quiet:
            server.logger = create_logger('geventwebsocket.logging')
            server.logger.setLevel(logging.INFO)
            server.logger.addHandler(logging.StreamHandler())

        server.serve_forever()

def websocket(callback):
    def wrapper(*args, **kwargs):
        callback(request.environ.get('wsgi.websocket'), *args, **kwargs)

    return wrapper




# Create the Bottle WSGI application.
bottle = Bottle()

# Define an handler for the root URL of our application.
@bottle.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return 'Hello World Bottle!!!!!'


# Define an handler for 404 errors.
@bottle.error(404)
def error_404(error):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.'

class InputRecords:

    def __init__(self):
        self.dialogue = {}
        self.message_to_client = []
        self.message_iter = 0

    def write(self):
        input_data = request.body.read().decode("utf-8")
        json_data = json.loads(input_data)
        inputs = json_data['inputs']
        raw_inputs = inputs[0]['rawInputs']
        raw_query = raw_inputs[0]['query'].split(" ")
        dialogue_key = raw_query[0]
        dialogue_value = raw_query[1:len(raw_query)]
        dialogue_value = " ".join(dialogue_value)
        self.dialogue['command'] = dialogue_key
        self.dialogue['text'] = dialogue_value
        dialogue_json = json.dumps(self.dialogue)
        loaded_dialogue = json.loads(dialogue_json)
        # print(loaded_dialogue)
        return loaded_dialogue

    def create_json(self, message):
        dialoge_clientID, dialogue_command, dialogue_filename, dialogue_value, dialogue_count = message.split(',')
        self.dialogue['clientID'] = dialoge_clientID
        self.dialogue['filename'] = dialogue_filename
        self.dialogue['command'] = dialogue_command
        self.dialogue['text'] = dialogue_value
        self.dialogue['counter'] = dialogue_count
        dialogue_json = json.dumps(self.dialogue)
        return dialogue_json

    def echo(self, ws):
        while True:
            msg = ws.receive()
            print(msg)
            if msg is not None:
                ws.send(msg)
            else:
                break

ssldict = {'keyfile': 'keys/privkey.pem', 'certfile': 'keys/cacert.pem'}

myApp = InputRecords()
bottle.route('/write', 'POST', myApp.write)
bottle.route('/websocket', 'GET', myApp.echo, apply=[websocket])

if __name__ == '__main__':
    # Get required port, default to 5000.
    port = os.environ.get('PORT', 5000)

    # Run the app.
    bottle.run(host='0.0.0.0', port=port)

# TODO: Add SSL
# bottle.run(host='0.0.0.0', port=8080, server=GeventWebSocketServer)

# server = WSGIServer(("0.0.0.0", 8080), bottle, handler_class=GeventWebSocketServer) #, **ssldict)
# server.serve_forever()
