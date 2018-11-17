"""`main` is the top level module for your Bottle application."""

# import the Bottle framework
from bottle import request, Bottle, abort, get
from bottle.ext.websocket import GeventWebSocketServer
from bottle.ext.websocket import websocket
from gevent.pywsgi import WSGIServer
import json

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


@get('/websocket', apply=[websocket])
def echo(ws):
    while True:
        msg = ws.receive()
        if msg is not None:
            ws.send(msg)
        else: break



class InputRecords:

    def __init__(self):
        self.dialogue = {}
        self.message_to_client = []
        self.message_iter = 0

    def create_json(self, message):
        dialoge_clientID, dialogue_command, dialogue_filename, dialogue_value, dialogue_count = message.split(',')
        self.dialogue['clientID'] = dialoge_clientID
        self.dialogue['filename'] = dialogue_filename
        self.dialogue['command'] = dialogue_command
        self.dialogue['text'] = dialogue_value
        self.dialogue['counter'] = dialogue_count
        dialogue_json = json.dumps(self.dialogue)
        return dialogue_json

ssldict = {'keyfile': 'keys/privkey.pem', 'certfile': 'keys/cacert.pem'}

myApp = InputRecords()
bottle.route('/write', 'POST', myApp.write)
# bottle.route('/websocket', 'GET', myApp.handle_websocket)

bottle.run(host='127.0.0.1', port=8080, server=GeventWebSocketServer)

# server = WSGIServer(("0.0.0.0", 8080), bottle, handler_class=GeventWebSocketServer) #, **ssldict)
# server.serve_forever()
