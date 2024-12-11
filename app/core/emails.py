# core/emails.py
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import Dict
from pydantic import EmailStr

async def send_test_email(to_email: EmailStr, smtp_settings: Dict) -> bool:
    """Send a test email"""
    try:
        # Create connection config from settings
        conf = ConnectionConfig(
            MAIL_SERVER=smtp_settings['MAIL_SERVER'],
            MAIL_PORT=smtp_settings['MAIL_PORT'],
            MAIL_USERNAME=smtp_settings['MAIL_USERNAME'],
            MAIL_PASSWORD=smtp_settings['MAIL_PASSWORD'],
            MAIL_FROM=smtp_settings['MAIL_FROM'],
            MAIL_FROM_NAME=smtp_settings['MAIL_FROM_NAME'],
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )

        # Create FastMail instance
        fastmail = FastMail(conf)

        # Create message
        message = MessageSchema(
            subject="Test Email from Scheduling App",
            recipients=[to_email],
            body="""
            This is a test email from your scheduling application.
            If you received this email, your email configuration is working correctly.
            """,
            subtype="plain"
        )

        # Send email
        await fastmail.send_message(message)
        return True
    except Exception as e:
        print(f"Error sending test email: {str(e)}")
        raise