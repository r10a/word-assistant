import os
import json
import redis
from flask import Flask, request, jsonify


REDIS_URL: str = os.environ['REDIS_URL']  # Get REDIS url on Heroku
# Uncomment below line if running on local machine
# REDIS_URL = "redis://h:p4a49c92f2f92f61555110cca953dd9b8fc55fe9736e8aa3d277ea93fa4abb0c0@ec2-54-158-0-180.compute-1.amazonaws.com:62409"
REDIS_SERVER: str = 'server'  # REDIS server channel name
REDIS_CLIENT: str = 'client'  # REDIS client channel name

# Create the Flask WSGI application.
app = Flask(__name__)
app.debug = 'DEBUG' in os.environ

redis = redis.from_url(REDIS_URL)  # attach to redis server running on REDIS_URL


# Define test handler for the root URL of application for testing if application is running
@app.route('/')
def hello():
    """
    Root method for testing if server is up
    :return: str
    """
    return "Hello world flask"


class Server:
    """ Class responsible for broadcasting google assistant messages to clients via REDIS """

    def __init__(self):
        self.pubsub = redis.pubsub()  # Attach to redis pubsub
        self.pubsub.subscribe(REDIS_CLIENT)  # Start listening to Client channel for acknowledgements

    def __iter_data(self):
        """
        Generator function for listening to acknowledgements from clients
        :yield: data
        """
        for message in self.pubsub.listen():  # Listen on client channel for ack. Blocks until ack is received
            data: str = message.get('data')  # extract ack
            if message['type'] == 'message':
                yield data

    def receive_from_ga(self):
        content = request.get_json()
        print("content", content)
        queryResult = content['queryResult']
        command = {'queryText': queryResult['queryText'], 'parameters': queryResult['parameters']}
        app.logger.info(u'Inserting message: {}'.format(command))
        redis.publish(REDIS_SERVER, json.dumps(command))
        ack = {}
        for data in self.__iter_data():
            app.logger.info(u'Received ack: {}'.format(data))
            ack = data
            break  # break on receiving ack

        print(ack)  # log ack
        #  prepare response to google assistant depending on if the operation completed successfully or not
        text: str = "Done. Please continue" if json.loads(ack)["completed"] else "Sorry. Something went wrong. Please try again."

        # response json to google assistant with required format
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


server = Server()  # create an instance of above Server class
# map receive_from_ga method from server class to /write url of server and set expected message type as POST
app.add_url_rule('/write', 'write', server.receive_from_ga, methods=['POST'])


if __name__ == '__main__':
    # Does not run on heroku server. Only on local
    app.run(host='127.0.0.1', port=5000, debug=True)  # Start server for local development
