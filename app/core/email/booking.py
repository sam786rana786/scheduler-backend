from typing import Dict, Any
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from ..config import get_settings
from .templates import get_booking_confirmation_template

settings = get_settings()

async def send_booking_confirmation(to_email: str, event_details: Dict[str, Any]) -> bool:
    """
    Send booking confirmation email to attendee
    
    Args:
        to_email: Recipient email address
        event_details: Dictionary containing event details
            {
                'title': str,
                'date': str,
                'time': str,
                'duration': str,
                'location': str,
                'host_name': str,
                'google_calendar_link': str (optional),
                'outlook_calendar_link': str (optional)
            }
    """
    try:
        # Create connection config
        conf = ConnectionConfig(
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )

        # Get email templates
        templates = get_booking_confirmation_template(event_details)

        # Create message
        message = MessageSchema(
            subject=f"Booking Confirmed: {event_details['title']}",
            recipients=[to_email],
            body=templates["html"],
            subtype="html",
            alternative_body=templates["text"]
        )

        # Send email
        fastmail = FastMail(conf)
        await fastmail.send_message(message)
        
        return True
    except Exception as e:
        print(f"Error sending booking confirmation email: {str(e)}")
        raise
