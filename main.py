from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import os
import aiofiles
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = FastAPI()

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
            message.add_attachment(file_data, "application/pdf", file.filename)

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)

        return JSONResponse({"status": "success", "message": "Email sent successfully!"})

    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)})

@app.get("/")
def home():
    return {"message": "SendDocs backend is running"}
