"""`main` is the top level module for your Bottle application."""

# import the Bottle framework
from bottle import request, Bottle
import json

# Create the Bottle WSGI application.
bottle = Bottle()
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


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

myApp = InputRecords()
bottle.route('/write', 'POST', myApp.write)