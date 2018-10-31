from docx import Document
import json
import os


# TODO: Add more functionality
class DocumentWriter:

    def __init__(self, docname):
        self._current_para = None
        self.error_code = 0
        self._document = Document()
        self._docname = docname

    def add_text(self, text):
        self._current_para.add_run(text=text)

    def add_heading(self, text):
        self._current_para = self._document.add_heading(text=text)

    def add_paragraph(self, text):
        self._current_para = self._document.add_paragraph(text=text)

    def save_document(self):
        self._document.save(self._docname)

def parse_message(message_from_gce):
    json_data = json.loads(message_from_gce)
    message_clientID = str(json_data['clientID'])
    message_filename = str(json_data['filename'])
    message_command = str(json_data['command'])
    message_value = str(json_data['text'])
    message_count = str(json_data['counter'])
    return message_clientID, message_filename, message_command, message_value, message_count

# TODO: Configure Websocket connection to Cloud server
from websocket import create_connection
ws = create_connection("ws://localhost:8080/websocket")
iter = 0

client_busy = False
client_online = True
message_from_cloud = []

while True:
    if not client_online:
        ws.send("client offline")
        print("client offline")

    if client_busy:
        ws.send("client busy")
        message_clientID, message_filename, message_command, message_value, message_count = parse_message(message_from_cloud)
        document_name = 'outputs/' + message_filename + '.docx'
        doc = DocumentWriter(docname=document_name)

        #Create a file
        if message_command == 'create':
            try:
                doc.add_paragraph(message_value)
                doc.save_document()
                ws.send("Message %s processed, 0" % message_count)
                client_busy = False
            except:
                ws.send("Message %s processed, 1" % message_count)
                client_busy = False

        # Edit an existing File
        if message_command == 'edit':
            try:
                doc.add_paragraph(message_value)
                doc.save_document()
                ws.send("Message %s processed, 0" % message_count)
                client_busy = False
            except:
                ws.send("Message %s processed, 1" % message_count)
                client_busy = False

        # Delete a file
        if message_command == 'delete':
            try:
                os.remove(document_name)
                ws.send("Message %s processed, 0" % message_count)
                client_busy = False
            except OSError:
                ws.send("Message %s processed, 1" % message_count)
                client_busy = False

    if not client_busy and client_online:
        print("Sending 'ready to receive from client'")
        ws.send("client_online and not busy")
        print("Sent to cloud")
        print("Waiting for data from cloud")
        message_from_cloud = ws.recv()
        print("Message Received from cloud")
        print(message_from_cloud)
        client_busy = True
