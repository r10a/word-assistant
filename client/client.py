from docx import Document
import json
import logging
import redis
import os

from uuid import getnode

REDIS_URL = "redis://h:p4a49c92f2f92f61555110cca953dd9b8fc55fe9736e8aa3d277ea93fa4abb0c0@ec2-54-158-0-180.compute-1.amazonaws.com:62409"
REDIS_SERVER = 'server'
REDIS_CLIENT = 'client'

redis = redis.from_url(REDIS_URL)


# TODO: Add more functionality
class DocumentWriter:

    def __init__(self, docname="generated.docx"):
        self._current_para = None
        self.error_code = 0
        self._document = Document()
        self._docname = docname

    def get_docname(self):
        return self._docname

    def add_text(self, text):
        if self._current_para is None:
            self.add_paragraph(text)
        else:
            self._current_para.add_run(text=text)

    def add_heading(self, text):
        self._current_para = self._document.add_heading(text=text)

    def add_paragraph(self, text):
        self._current_para = self._document.add_paragraph(text=text)

    def save_document(self):
        self._document.save(self._docname)


class CommandHandler:

    def __init__(self):
        self.doc = DocumentWriter()
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_SERVER)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                yield data

    def run(self):
        """Listens for new commands in Redis, and executes them."""
        for data in self.__iter_data():
            self.on_message(data)

    def respond(self, completed):
        ack = {
            "id": getnode(),
            "completed": completed
        }
        redis.publish(REDIS_CLIENT, json.dumps(ack))

    def on_message(self, message):
        print("command", message)
        command, parameters = self.parse_message(message)
        if command == 'type':
            try:
                print("adding", parameters)
                self.doc.add_text(parameters)
                self.doc.save_document()
                self.respond(True)
            except Exception as e:
                logging.error('Failed to add to document: ' + str(e))
                self.respond(False)

        if command == 'create':
            try:
                print("creating", parameters)
                self.doc = DocumentWriter(docname=parameters)
                self.doc.save_document()
                self.respond(True)
            except Exception as e:
                logging.error('Failed to save document: ' + str(e))
                self.respond(False)

        if command == 'delete':
            try:
                print("deleting", parameters)
                os.remove(self.doc.get_docname())
                self.respond(True)
            except Exception as e:
                logging.error('Failed to delete document: ' + str(e))
                self.respond(False)

    def parse_message(self, command):
        print("command", command)
        json_data = json.loads(command)
        query = str(json_data['queryText'])
        parameters = json_data['parameters']['text']
        command = query.split()[0]
        return command, parameters


ch = CommandHandler()
ch.run()