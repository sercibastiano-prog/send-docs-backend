from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse
import os
import aiofiles
import base64

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail,
    Attachment,
    FileContent,
    FileName,
    FileType,
    Disposition,
)

app = FastAPI()


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
        # Salva temporaneamente il file
        save_path = f"/tmp/{file.filename}"
        async with aiofiles.open(save_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        # Leggi i bytes per l'allegato
        with open(save_path, "rb") as f:
            file_data = f.read()

        # Crea l'email
        message = Mail(
            from_email=sender,
            to_emails=RECEIVER_EMAIL,
            subject="New Document Received",
            html_content=f"Document {file.filename} received from {sender}.",
        )

        # Allegato in base64 per SendGrid
        encoded = base64.b64encode(file_data).decode()
        attachment = Attachment(
            FileContent(encoded),
            FileName(file.filename),
            FileType("application/pdf"),
            Disposition("attachment"),
        )
        message.attachment = attachment

        # Invia con SendGrid
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        resp = sg.send(message)

        return JSONResponse(
            {"status": "success", "message": "Email sent successfully!", "sendgrid_status": resp.status_code}
        )

    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)})


@app.get("/")
def home():
    return {"message": "SendDocs backend is running"}
