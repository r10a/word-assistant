"""`main` is the top level module for your Bottle application."""

# import the Bottle framework
from bottle import request, Bottle, abort
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
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


class InputRecords:

    def __init__(self):
        self.dialogue = {}

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

    def handle_websocket(self):
        wsock = request.environ.get('wsgi.websocket')
        if not wsock:
            abort(400, 'Expected WebSocket request.')

        while True:
            try:
                message = wsock.receive()
                wsock.send("Your message was: %r" % message)
            except WebSocketError:
                break


myApp = InputRecords()
bottle.route('/write', 'POST', myApp.write)
bottle.route('/websocket', 'GET', myApp.handle_websocket)

server = WSGIServer(("0.0.0.0", 8080), bottle, handler_class=WebSocketHandler)
server.serve_forever()
