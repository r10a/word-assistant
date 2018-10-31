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

    def handle_websocket(self):
        wsock = request.environ.get('wsgi.websocket')
        if not wsock:
            abort(400, 'Expected WebSocket request.')

        ready_to_receive = False
        waiting_for_client_ack = False

        while True:
            try:
                message_from_client = str(wsock.receive())

                if message_from_client == 'client offline':
                    print('client offline')
                    ready_to_receive = False

                if message_from_client == 'client_online and not busy':
                    ready_to_receive = True

                if message_from_client == 'client busy':
                    waiting_for_client_ack = True

                if message_from_client.split(',')[0] == ('Message %d processed' % self.message_iter):
                    error_code = int(message_from_client.split(',')[1])
                    if error_code == 0:
                        print('Word File succesfully updated for message %s' % self.message_to_client[self.message_iter])
                        waiting_for_client_ack = False
                        ready_to_receive = True
                        self.message_iter += 1
                    else:
                        print('Word File update failure for message %s' % self.message_to_client[self.message_iter])
                        # based on the user feedback this message on the iter needs needs to be updated and resent. Current logic ignores the error and moves forward with next message
                        waiting_for_client_ack = False
                        ready_to_receive = True
                        self.message_iter += 1

                if ready_to_receive and not waiting_for_client_ack:
                    print('Sending from cloud')
                    send_message_to_client = self.create_json(self.message_to_client[self.message_iter])
                    wsock.send(send_message_to_client)
                    print('Message sent %s' % send_message_to_client)
                    waiting_for_client_ack = True

                else:
                    continue

            except WebSocketError:
                print('Sending to client Error')
                break

myApp = InputRecords()
# bottle.route('/write', 'POST', myApp.write)

# wordx_cly means xth file on client y
word_commands = ["1,create,word1_cl1,My First Line on client 1,0",
                 "1,edit,word1_cl1, My Second Line on client 1,1",
                 "2,create,word1_cl2,My Second File First Line,2",
                 "1,delete,word1_cl1, ,3",
                 "2,delete,word2_cl2, ,4",
                 "1,edit,word1_cl1,My Third Line on client 1,5",
                 "2,edit,word1_cl2,My Third Line on client 2,6",
                 "2,create,word4_cl2,My First Line on client 2, 7"]

for iter in range(len(word_commands)):
    myApp.message_to_client.append(word_commands[iter])

bottle.route('/websocket', 'GET', myApp.handle_websocket)

server = WSGIServer(("localhost", 8080), bottle, handler_class=WebSocketHandler)
server.serve_forever()
