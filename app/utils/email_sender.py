import yagmail
import os

def send_email_with_pdf(receiver_email: str, pdf_path: str):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    yag = yagmail.SMTP(user=sender_email, password=sender_password)
    yag.send(
        to=receiver_email,
        subject="Downtime Report",
        contents="Please find attached the latest downtime report.",
        attachments=pdf_path
    )
    return {"status": "Email sent successfully"}
