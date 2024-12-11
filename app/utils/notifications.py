# utils/notifications.py
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from twilio.rest import Client
from datetime import datetime
from typing import Dict, Any

async def send_cancellation_email(to_email: str, event_title: str, event_time: datetime, reason: str, email_settings: Dict[str, Any]):
    config = {
        'MAIL_SERVER': email_settings['smtp_server'],
        'MAIL_PORT': email_settings['smtp_port'],
        'MAIL_USERNAME': email_settings['smtp_username'],
        'MAIL_PASSWORD': email_settings['smtp_password'],
        'MAIL_FROM': email_settings['from_email'],
        'MAIL_FROM_NAME': email_settings['from_name']
    }
    if not config:
        print("Email configuration is invalid or missing")
        return False

    try:
        conf = ConnectionConfig(
            MAIL_SERVER=config['MAIL_SERVER'],
            MAIL_PORT=config['MAIL_PORT'],
            MAIL_USERNAME=config['MAIL_USERNAME'],
            MAIL_PASSWORD=config['MAIL_PASSWORD'],
            MAIL_FROM=config['MAIL_FROM'],
            MAIL_FROM_NAME=config['MAIL_FROM_NAME'],
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        fastmail = FastMail(conf)
        message = MessageSchema(
            subject=f"Event Cancelled: {event_title}",
            recipients=[to_email],
            body=f"""
            Your event has been cancelled.
            
            Event: {event_title}
            Time: {event_time.strftime('%B %d, %Y at %I:%M %p')}
            Reason: {reason}
            
            We apologize for any inconvenience.
            """,
            subtype="plain"
        )
        
        await fastmail.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send cancellation email: {str(e)}")
        return False

async def send_cancellation_sms(
    to_phone: str,
    event_title: str,
    event_time: datetime,
    reason: str,
    sms_settings: Dict
):
    """Send cancellation SMS using user's SMS settings"""
    try:
        # Create Twilio client with user's settings
        client = Client(
            sms_settings.get('account_sid'),
            sms_settings.get('auth_token')
        )

        message = client.messages.create(
            body=f"""
            Your event '{event_title}' scheduled for {event_time.strftime('%B %d at %I:%M %p')} has been cancelled.
            Reason: {reason}
            """,
            from_=sms_settings.get('from_number'),
            to=to_phone
        )
        
        return True
    except Exception as e:
        print(f"Failed to send cancellation SMS: {str(e)}")
        return False

async def send_notifications(
    event,
    reason: str,
    user_settings,
    profile,
    attendee_email: str,
    attendee_phone: str = None
):
    """Centralized notification sending function"""
    notification_results = {
        'email_sent': False,
        'sms_sent': False
    }

    # Check if email notifications are enabled
    if (user_settings.notification_settings.get('email', {}).get('enabled') and 
        user_settings.notification_settings.get('email', {}).get('canceledBooking')):
        
        notification_results['email_sent'] = await send_cancellation_email(
            to_email=attendee_email,
            event_title=event.title,
            event_time=event.start_time,
            reason=reason,
            email_settings=user_settings.email_settings
        )

    # Check if SMS notifications are enabled and phone number is available
    if (profile.phone and 
        user_settings.notification_settings.get('sms', {}).get('enabled') and
        user_settings.sms_settings.get('provider') == 'twilio'):
        
        notification_results['sms_sent'] = await send_cancellation_sms(
            to_phone=profile.phone,
            event_title=event.title,
            event_time=event.start_time,
            reason=reason,
            sms_settings=user_settings.sms_settings
        )

    return notification_results

async def send_booking_confirmation_email(
    to_email: str,
    event_title: str,
    event_time: datetime,
    attendee_name: str,
    host_name: str,
    location: str,
    email_settings: Dict[str, Any]
) -> bool:
    """Send booking confirmation email to attendee"""
    config={
        'MAIL_SERVER': email_settings['smtp_server'],
        'MAIL_PORT': email_settings['smtp_port'],
        'MAIL_USERNAME': email_settings['smtp_username'],
        'MAIL_PASSWORD': email_settings['smtp_password'],
        'MAIL_FROM': email_settings['from_email'],
        'MAIL_FROM_NAME': email_settings['from_name']
    }
    if not config:
        print("Email configuration is invalid or missing")
        return False

    try:
        conf = ConnectionConfig(
            MAIL_SERVER=config['MAIL_SERVER'],
            MAIL_PORT=config['MAIL_PORT'],
            MAIL_USERNAME=config['MAIL_USERNAME'],
            MAIL_PASSWORD=config['MAIL_PASSWORD'],
            MAIL_FROM=config['MAIL_FROM'],
            MAIL_FROM_NAME=config['MAIL_FROM_NAME'],
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        fastmail = FastMail(conf)
        message = MessageSchema(
            subject=f"Booking Confirmation: {event_title}",
            recipients=[to_email],
            body=f"""
            Dear {attendee_name},

            Your booking has been confirmed!

            Event: {event_title}
            Time: {event_time.strftime('%B %d, %Y at %I:%M %p')}
            Location: {location}
            Host: {host_name}

            Thank you for booking with us.
            """,
            subtype="plain"
        )
        
        await fastmail.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send booking confirmation email: {str(e)}")
        return False

async def send_booking_confirmation_sms(
    to_phone: str,
    event_title: str,
    event_time: datetime,
    sms_settings: Dict[str, Any]
) -> bool:
    """Send booking confirmation SMS to attendee"""
    if not all([
        sms_settings.get('account_sid'),
        sms_settings.get('auth_token'),
        sms_settings.get('from_number')
    ]):
        print("SMS configuration is invalid or missing")
        return False

    try:
        client = Client(
            sms_settings['account_sid'],
            sms_settings['auth_token']
        )
        
        message = client.messages.create(
            body=f"""
            Your booking for {event_title} on {event_time.strftime('%B %d at %I:%M %p')} is confirmed.
            """,
            from_=sms_settings['from_number'],
            to=to_phone
        )
        return True
    except Exception as e:
        print(f"Failed to send booking confirmation SMS: {str(e)}")
        return False

__all__ = [
    'send_booking_confirmation_email',
    'send_booking_confirmation_sms',
    'send_cancellation_email',
    'send_cancellation_sms'
]