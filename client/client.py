from docx import Document


# TODO: Add more functionality
class DocumentWriter:

    def __init__(self, docname=None):
        self._current_para = None
        if docname:
            self._document = Document(docname)
            self._docname = docname
        else:
            self._document = Document()
            self._docname = "generated.docx"
        self.add_paragraph(text="")

    def add_text(self, text):
        self._current_para.add_run(text=text)

    def add_heading(self, text):
        self._current_para = self._document.add_heading(text=text)

    def add_paragraph(self, text):
        self._current_para = self._document.add_paragraph(text=text)

    def save_document(self):
        self._document.save(self._docname)


name = "demo.docx"

doc = DocumentWriter()
doc.add_heading("Hello World!")
doc.add_paragraph("New Paragraph \n")
doc.add_text("This is so Awesome1!")
doc.add_text("This is so Awesome2!")
doc.add_text("This is so Awesome3!")
doc.add_text("This is so Awesome4!")
doc.save_document()


# TODO: Configure Websocket connection to Cloud server
# from websocket import create_connection
# ws = create_connection("ws://35.237.62.22:8080/websocket")
# print("Sending 'Hello, World'...")
# ws.send("Hello, World")
# print("Sent")
# print("Receiving...")
# result = ws.recv()
# print("Received '%s'" % result)
# ws.close()
