from twilio.rest import Client
import os

# Load from environment variables
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")
ALERT_PHONE = os.getenv("ALERT_PHONE_NUMBER")  # Maintenance team phone

client = Client(TWILIO_SID, TWILIO_AUTH)

def send_alert(machine_temp, vibration, probability):
    message = f"⚠️ Downtime Risk Alert!\nTemp: {machine_temp}°C\nVibration: {vibration}\nRisk: {probability*100:.2f}%"
    client.messages.create(
        body=message,
        from_=TWILIO_PHONE,
        to=ALERT_PHONE
    )
