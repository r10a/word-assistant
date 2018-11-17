"""`main` is the top level module for your Bottle application."""

# import the Bottle framework
from bottle import request, Bottle, abort, get
from bottle.ext.websocket import GeventWebSocketServer
from bottle.ext.websocket import websocket
from gevent.pywsgi import WSGIServer
import json
import numpy as np

# Create the Bottle WSGI application.
bottle = Bottle()

users = set()


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
        self.user_list = np.zeros((1, 100))
        self.ack_received = False
        self.first_message = True
        self.ack_count = 0
        self.all_msg_processed = False

    def create_json(self, message):
        dialoge_clientID, dialogue_command, dialogue_filename, dialogue_value, dialogue_count = message.split(',')
        self.dialogue['clientID'] = dialoge_clientID
        self.dialogue['filename'] = dialogue_filename
        self.dialogue['command'] = dialogue_command
        self.dialogue['text'] = dialogue_value
        self.dialogue['counter'] = dialogue_count
        dialogue_json = json.dumps(self.dialogue)
        return dialogue_json

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

    def chat(self, ws):
        print('in echo')
        users.add(ws)
        while True:
            # Try to receive acknowledgments from the clients
            msg = ws.receive()
            if msg is not None:
                print('Acknowledgement received from Client')
                print(msg)
                if msg[0:5] == 'Hello':
                    print('New client joined \n' + msg)
                    client_id = int(msg.split(',')[1])
                    self.user_list[0,client_id] = 1
                if msg[0:3] == 'Bye':
                    print('Client leaving' + msg)
                    client_id = msg.split(',')[1]
                    self.user_list[client_id] = 0
                elif msg[0:3] == 'Ack':
                    self.ack_received = True
                    self.message_iter += 1
                    self.ack_count += 1

            if self.message_iter == len(self.message_to_client):
                self.all_msg_processed = True

            if not self.all_msg_processed:
                msg_to_client = self.message_to_client[self.message_iter]
                if self.ack_received or self.first_message:
                # if self.message_iter < len(self.message_to_client):
                    # Send message one by one to all users connected
                    if self.user_list[0, int(msg_to_client.split(',')[0])] == 1:
                        send_message_to_client = self.create_json(msg_to_client)
                        print(send_message_to_client)
                        if send_message_to_client is not None:
                            for u in users:
                                u.send(send_message_to_client)
                            self.ack_received = False
                        else:
                            break
                    else:
                        print('Client %d is offline' % int(msg_to_client.split(',')[0]))
            else:
                users.remove(ws)


ssldict = {'keyfile': 'keys/privkey.pem', 'certfile': 'keys/cacert.pem'}

myApp = InputRecords()
# wordx_cly means xth file on client y
# word_commands = ["1,create,word1_cl1,My First Line on client 1,0",
#                  "1,edit,word1_cl1,My Second Line on client 1,1",
#                  "2,create,word1_cl2,My Second File First Line,2",
#                  "1,delete,word1_cl1, ,3",
#                  "2,delete,word2_cl2, ,4",
#                  "1,edit,word1_cl1,My Third Line on client 1,5",
#                  "2,edit,word1_cl2,My Third Line on client 2,6",
#                  "2,create,word4_cl2,My First Line on client 2, 7"]
word_commands = ["1,create,word1_cl1,My First Line on client 1,0",
                 "1,edit,word1_cl1,My Second Line on client 1,1",]

for iter in range(len(word_commands)):
    myApp.message_to_client.append(word_commands[iter])

bottle.route('/websocket', 'GET', myApp.chat, apply=[websocket])

bottle.run(host='127.0.0.1', port=8080, server=GeventWebSocketServer)
