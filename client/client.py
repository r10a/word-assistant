import json
import logging
import redis
from pywinauto.application import Application
from wakeonlan import send_magic_packet
from subprocess import Popen

REDIS_URL = "redis://h:p4a49c92f2f92f61555110cca953dd9b8fc55fe9736e8aa3d277ea93fa4abb0c0@ec2-54-158-0-180.compute-1.amazonaws.com:62409"
REDIS_SERVER = 'server'
REDIS_CLIENT = 'client'

ip = '129.107.116.129'  # IP address of the client system to boot and shut down

redis = redis.from_url(REDIS_URL)  # attach to Redis server running on REDIS_URL


class CommandHandler:
    """
    This class handles all the messages from the Heroku Cloud server
    """

    def __init__(self):
        """
        This is the class constructor that initialises the Redis server for publish-subscribe protocol and the initial
        document to None
        """
        self.doc: str = None  # variable to store the document object handle from pywinauto library
        self.new_window: object = None  # object variable to store a document window
        self.document_open: str = False  # variable to keep track of the status of the document(open/close)
        self.username: str = 'saif'  # username variable initialized to the client username
        self.pubsub: object = redis.pubsub()  # redis publish-subscribe protocol object
        self.pubsub.subscribe(REDIS_SERVER)  # redis pub-sub protocol initialized to listen to 'REDIS_SERVER' channel

    def open_doc(self):
        """
        This function opens a MS Word document from the client system and opens a blank document
        """
        self.doc = Application().start(cmd_line=u'C:\\Program Files (x86)\\Microsoft Office\\root\\Office16\\WINWORD.EXE')
        self.new_window = self.doc.window(top_level_only=True, active_only=True, class_name='OpusApp')
        self.new_window.type_keys(r'{ENTER}')  # opens a blank document using ENTER key press
        self.document_open = True  # sets document status to open
        self.respond(True, "")  # responds to server with 'True'


    def __iter_data(self):
        """
        Listens to each and every messages from the subcribed Redis channel and store the message into a variable
        :yield: generator
        """
        for message in self.pubsub.listen():  # listens on server channel for commands. Blocks until command is received
            data = message.get('data')  # extracts command
            if message['type'] == 'message':
                yield data  # yields command if the type is 'message'

    def run(self):
        """Listens for new commands in Redis, and executes them."""
        for data in self.__iter_data():
            self.on_message(data)

    def respond(self, completed, parameters):
        """
        Publishes the acknowledgement from the client to Redis channel in JSON format
        :param completed: stores the status of the command
        :param parameters: stores the command executed
        """
        ack = {
            "id": self.username,
            "completed": completed,
            "parameters": parameters
        }
        print("sending response: ", ack)
        redis.publish(REDIS_CLIENT, json.dumps(ack))  # sends acknowledgement to server

    def save_doc(self):
        """
        Saves a MS Word document simulating key press
        """
        self.new_window.type_keys(r'%FAO{ENTER}')

    def on_message(self, message):
        """
        Takes different actions based on the commands in the input JSON message object received from the
        Heroku Cloud Server
        :param message: Input JSON message object
        """
        command, parameters = self.parse_message(message)  # stores the return values from parse_message message
        print("Command: ", command, " Params: ", parameters)
        if command is None:  # if the command not meant for this client system
            return None

        if command.lower() in ['open', 'create']:  # Checks if the command received is 'open' or 'create'
            try:
                print("opening document")
                self.open_doc()  # calls the function to open the MS Word document
                self.respond(True, "Opened")  # responds successfully
            except Exception as e:  # handles exception if any
                logging.error('Failed to open document: ' + str(e))
                self.respond(False, "Not Opened")  # responds that operation failed

        if command.lower() in ['type', 'write']:  # Checks if the command received is 'type' or 'write'
            try:
                if not self.document_open:
                    self.open_doc()  # opens the document if not open
                print("adding", parameters)
                # types the command parameters by simulating key presses
                self.new_window.type_keys(parameters.replace(" ", "{SPACE}") + ".{SPACE}")
                self.respond(True, parameters)  # responds successfully
            except Exception as e:
                logging.error('Failed to add to document: ' + str(e))
                self.respond(False, parameters)  # responds that operation failed

        if command.lower() == 'save':  # checks if the command is to 'save' the document
            try:
                print("saving")
                self.save_doc()  # saves the document
                self.respond(True, "Saved")  # responds successfully
            except Exception as e:
                logging.error('Failed to save document: ' + str(e))
                self.respond(False, "Not saved")  # responds that operation failed

        if command.lower() in ['close', 'finish']:  # checks if the command is to 'close' the document
            try:
                print("closing")
                self.save_doc()  # calls the function to save the document
                self.new_window.type_keys(r'%{F4}')  # close the document simulating ALT+F4 key press
                self.document_open = False  # sets the document status to closed
                self.respond(True, "Closed")  # responds successfully
            except Exception as e:
                logging.error('Failed to save document: ' + str(e))
                self.respond(False, "Not Closed")  # responds that operation failed

        if command.lower() in ['boot', 'power on']:  # check if the command is to 'boot' the client system
            # sends magic packets to a particular system using it's unique MAC address and IP within the same wifi
            # network
            send_magic_packet('10.7B.44.93.AC.41', ip_address=ip, port=9)
            self.respond(True, "Booting up")  # responds successfully

        # checks if the command is to shut down the client system
        if command.lower() in ['off', 'turn off', 'shutdown', 'power off']:
            # connects to runs a Linux system through it's IP using plink and runs a shell script to shut down
            Popen("plink root@129.107.116.129 -pw root /home/rohit/shutdown.sh")
            self.respond(True, "shutting down")  # responds successfully

    def parse_message(self, command):
        """
        Parses a JSON object to find the 'command' and corresponding parameters
        to process
        :param command: JSON object received from Heroku Cloud Server
        """
        print("command", command)
        print(command)
        json_data = json.loads(command)
        iuser = None
        if 'name' in json_data['parameters']:
            iuser = json_data['parameters']['name'].lower()
            print("username: ", iuser)
        else:
            command = str(json_data['queryText'])
            return command, None

        if iuser and self.username == iuser or iuser == 'all':
            query = str(json_data['queryText'])
            parameters = json_data['parameters']['text'] if 'text' in json_data['parameters'] else None
            command = query.split()[0]
            return command, parameters
        else:
            return None, None


ch = CommandHandler()
ch.run()  # starts client
