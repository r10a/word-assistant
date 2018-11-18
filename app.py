import os
import json
import logging
import redis
import gevent
from flask import Flask, request
from flask_restful import Resource, Api
from flask_sockets import Sockets

REDIS_URL = os.environ['REDIS_URL']
REDIS_CHAN = 'word-assistant'


# Create the Flask WSGI application.
app = Flask(__name__)
app.debug = 'DEBUG' in os.environ

sockets = Sockets(app)
api = Api(app)
redis = redis.from_url(REDIS_URL)

class ClientBackend(object):
    """Interface for registering and updating WebSocket clients."""

    def __init__(self):
        self.clients = list()
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_CHAN)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                app.logger.info(u'Sending message: {}'.format(data))
                yield data

    def register(self, client):
        """Register a WebSocket connection for Redis updates."""
        self.clients.append(client)

    def send(self, client, data):
        """Send given data to the registered client.
        Automatically discards invalid connections."""
        try:
            client.send(data)
        except Exception:
            self.clients.remove(client)

    def run(self):
        """Listens for new messages in Redis, and sends them to clients."""
        for data in self.__iter_data():
            for client in self.clients:
                gevent.spawn(self.send, client, data)

    def start(self):
        """Maintains Redis subscription in the background."""
        gevent.spawn(self.run)

clients = ClientBackend()
clients.start()


# Define an handler for the root URL of our application.
class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}


class InputRecords(Resource):

    def post(self):
        args = request.args
        print(args)  # For debugging
        # input_data = request.body.read().decode("utf-8")
        # json_data = json.loads(input_data)
        # inputs = json_data['inputs']
        # raw_inputs = inputs[0]['rawInputs']
        # raw_query = raw_inputs[0]['query'].split(" ")
        # dialogue_key = raw_query[0]
        # dialogue_value = raw_query[1:len(raw_query)]
        # dialogue_value = " ".join(dialogue_value)
        # self.dialogue['command'] = dialogue_key
        # self.dialogue['text'] = dialogue_value
        # dialogue_json = json.dumps(self.dialogue)
        # loaded_dialogue = json.loads(dialogue_json)
        # print(loaded_dialogue)
        # app.logger.info(u'Inserting message: {}'.format(input_data))
        # redis.publish(REDIS_CHAN, json.dumps(input_data))

    # def create_json(self, message):
    #     dialoge_clientID, dialogue_command, dialogue_filename, dialogue_value, dialogue_count = message.split(',')
    #     self.dialogue['clientID'] = dialoge_clientID
    #     self.dialogue['filename'] = dialogue_filename
    #     self.dialogue['command'] = dialogue_command
    #     self.dialogue['text'] = dialogue_value
    #     self.dialogue['counter'] = dialogue_count
    #     dialogue_json = json.dumps(self.dialogue)
    #     return dialogue_json

api.add_resource(HelloWorld, '/')
api.add_resource(InputRecords, '/write')

@sockets.route('/receive')
def outbox(ws):
    """Sends outgoing chat messages, via `ClientBackend`."""
    clients.register(ws)

    while not ws.closed:
        # Context switch while `ChatBackend.start` is running in the background.
        gevent.sleep(0.1)


if __name__ == '__main__':
    app.run(debug=True)