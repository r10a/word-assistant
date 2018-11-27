import json
import logging
import redis
import os
from pywinauto.application import Application
import getpass

from uuid import getnode

REDIS_URL = "redis://h:p4a49c92f2f92f61555110cca953dd9b8fc55fe9736e8aa3d277ea93fa4abb0c0@ec2-54-158-0-180.compute-1.amazonaws.com:62409"
REDIS_SERVER = 'server'
REDIS_CLIENT = 'client'

redis = redis.from_url(REDIS_URL)


class CommandHandler:

    def __init__(self):
        self.doc = None
        self.new_window = None
        self.document_open = False
        self.username = self.get_username()[0:6]
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_SERVER)

    def open_doc(self):
        self.doc = Application(backend='uia').start("C:\\Program Files\\Microsoft Office\\Office16\\WINWORD.EXE", timeout=50)
        self.new_window = self.doc.window(top_level_only=True, active_only=True, class_name='OpusApp')
        self.document_open = True
        self.respond(True, "")

    def get_username(self):
        return getpass.getuser()

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                yield data

    def run(self):
        """Listens for new commands in Redis, and executes them."""
        for data in self.__iter_data():
            self.on_message(data)

    def respond(self, completed, parameters):
        ack = {
            "id": getnode(),
            "completed": completed,
            "parameters": parameters
        }
        print(ack)
        redis.publish(REDIS_CLIENT, json.dumps(ack))

    def save_doc(self):
        self.new_window.type_keys(r'%FAO{ENTER}')

    def on_message(self, message):
        command, parameters = self.parse_message(message)
        print(command, parameters)
        if command is None:
            return None

        if command.lower() == 'open':
            try:
                print("opening document")
                self.open_doc()
                self.respond(True, "Opened")
            except Exception as e:
                logging.error('Failed to open document: ' + str(e))
                self.respond(False, "Not Opened")

        if command.lower() in ['type', 'write']:
            try:
                print(self.username)
                if not self.document_open:
                    self.open_doc()
                print("adding", parameters)
                self.new_window.type_keys(parameters.replace(" ", "{SPACE}") + ".{SPACE}")
                self.respond(True, parameters)
            except Exception as e:
                logging.error('Failed to add to document: ' + str(e))
                self.respond(False, parameters)

        if command.lower() == 'delete':  # TODO: Implement
            try:
                print("deleting", parameters)
                os.remove(self.doc.get_docname())
                self.respond(True, "Deleted")
            except Exception as e:
                logging.error('Failed to delete document: ' + str(e))
                self.respond(False, "Not Deleted")

        if command.lower() == 'save':
            try:
                print("saving")
                self.save_doc()
                self.respond(True, "Saved")
            except Exception as e:
                logging.error('Failed to save document: ' + str(e))
                self.respond(False, "Not saved")

        if command.lower() in ['close', 'finish']:
            try:
                print("closing")
                self.save_doc()
                self.new_window.type_keys(r'%{F4}')
                self.document_open = False
                self.respond(True, "Closed")
            except Exception as e:
                logging.error('Failed to save document: ' + str(e))
                self.respond(False, "Not Closed")

    def parse_message(self, command):
        print("command", command)
        json_data = json.loads(command)
        parameters = None
        command = None
        iuser = json_data['parameters']['name'].lower()
        if self.username == iuser or iuser == 'all':
            query = str(json_data['queryText'])
            parameters = json_data['parameters']['text'] if json_data['parameters'] else None
            command = query.split()[0]
            return command, parameters
        else:
            return None, None



ch = CommandHandler()
ch.run()