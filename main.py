from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import os
import aiofiles
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = FastAPI()

from fastapi.responses import HTMLResponse

@app.get("/form", response_class=HTMLResponse)
def upload_form():
    return """
    <html><body>
    <h3>Upload documento</h3>
    <form action="/send-document/" method="post" enctype="multipart/form-data">
      Mittente (email): <input type="email" name="sender" value="noreply@senddocs.local" required/><br/><br/>
      File (PDF): <input type="file" name="file" required/><br/><br/>
      <button type="submit">Invia</button>
    </form>
    </body></html>
    """


SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "office@company.com")

@app.post("/send-document/")
async def send_document(file: UploadFile, sender: str = Form(...)):
    try:
        save_path = f"/tmp/{file.filename}"
        async with aiofiles.open(save_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        message = Mail(
            from_email=sender,
            to_emails=RECEIVER_EMAIL,
            subject="New Document Received",
            html_content=f"Document {file.filename} received from {sender}."
        )

        with open(save_path, "rb") as f:
            file_data = f.read()
            from sendgrid.helpers.mail import Attachment, FileContent, FileName, FileType, Disposition
import base64

encoded = base64.b64encode(file_data).decode()
attachment = Attachment(
    FileContent(encoded),
    FileName(file.filename),
    FileType('application/pdf'),
    Disposition('attachment')
)
message.attachment = attachment


        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)

        return JSONResponse({"status": "success", "message": "Email sent successfully!"})

    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)})

@app.get("/")
def home():
    return {"message": "SendDocs backend is running"}
