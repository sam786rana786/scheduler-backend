from typing import Optional, Dict, Any
import requests
from twilio.rest import Client
from .config import get_settings

settings = get_settings()

def send_sms(to: str, message: str, config: Dict[str, Any]) -> bool:
    """
    Send SMS using configured provider
    """
    try:
        if config.provider == "twilio":
            return _send_twilio_sms(to, message, config)
        elif config.provider == "custom":
            return _send_custom_sms(to, message, config)
        else:
            raise ValueError(f"Unsupported SMS provider: {config.provider}")
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        raise

def _send_twilio_sms(to: str, message: str, config: Dict[str, Any]) -> bool:
    """
    Send SMS using Twilio
    """
    try:
        client = Client(config.account_sid, config.auth_token)
        message = client.messages.create(
            body=message,
            from_=config.from_number,
            to=to
        )
        return True
    except Exception as e:
        print(f"Twilio SMS error: {str(e)}")
        raise

def _send_custom_sms(to: str, message: str, config: Dict[str, Any]) -> bool:
    """
    Send SMS using custom API
    """
    try:
        response = requests.post(
            config.api_url,
            headers={"Authorization": f"Bearer {config.api_key}"},
            json={
                "to": to,
                "message": message
            }
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Custom SMS API error: {str(e)}")
        raise

def send_email(
    to: str,
    subject: str,
    body: str,
    html: Optional[str] = None,
    attachments: Optional[list] = None
) -> bool:
    """
    Send email using configured email provider
    """
    # Implement email sending logic here
    # This is a placeholder for future implementation
    pass