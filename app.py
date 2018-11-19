import os
import json
from builtins import print
import redis
from flask import Flask, request, jsonify
from flask_sockets import Sockets


REDIS_URL = os.environ['REDIS_URL']
# REDIS_URL = "redis://h:p4a49c92f2f92f61555110cca953dd9b8fc55fe9736e8aa3d277ea93fa4abb0c0@ec2-54-158-0-180.compute-1.amazonaws.com:62409"
REDIS_SERVER = 'server'
REDIS_CLIENT = 'client'

# Create the Flask WSGI application.
app = Flask(__name__)
app.debug = 'DEBUG' in os.environ

sockets = Sockets(app)
redis = redis.from_url(REDIS_URL)


# Define an handler for the root URL of our application.
@app.route('/')
def hello():
    return "Hello world flask"


class InputRecords:

    def __init__(self):
        self.clients = {}
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_CLIENT)

    def register(self, client):
        """Register a WebSocket connection for Redis updates."""
        uid = client.receive()
        app.logger.info('Client connected with id: ' + str(uid))
        self.clients[uid] = client

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                app.logger.info(u'Received ack: {}'.format(data))
                yield data

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
        redis.publish(REDIS_SERVER, json.dumps(command))
        ack = {}
        for data in self.__iter_data():
            ack = data
            break

        print(ack)
        text = "Done. Please continue" if json.loads(ack)["completed"] else "Sorry. Something went wrong. Please try again."

        return jsonify({
            "payload": {
                "google": {
                    "expectUserResponse": True,
                    "richResponse": {
                        "items": [
                            {
                                "simpleResponse": {
                                    "textToSpeech": text
                                }
                            }
                        ]
                    }
                }
            }
        })


input = InputRecords()
app.add_url_rule('/write', 'write', input.receive_from_ga, methods=['POST'])


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)