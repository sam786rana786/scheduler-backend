# core/sms.py
from typing import Dict, Optional
from twilio.rest import Client
import requests


class SMSService:
    def __init__(self, settings: Dict):
        self.settings = settings
        self.provider = settings.get('provider')
        
        if self.provider == 'twilio':
            self.client = Client(
                settings.get('account_sid'),
                settings.get('auth_token')
            )
        elif self.provider == 'custom':
            self.api_url = settings.get('api_url')
            self.api_key = settings.get('api_key')

    async def send_sms(self, to: str, message: str) -> bool:
        """Send SMS using configured provider"""
        try:
            if self.provider == 'twilio':
                return await self._send_twilio_sms(to, message)
            elif self.provider == 'custom':
                return await self._send_custom_sms(to, message)
            else:
                raise ValueError(f"Unsupported SMS provider: {self.provider}")
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            raise

    async def _send_twilio_sms(self, to: str, message: str) -> bool:
        """Send SMS using Twilio"""
        try:
            if not all([
                self.settings.get('account_sid'),
                self.settings.get('auth_token'),
                self.settings.get('from_number')
            ]):
                raise ValueError("Missing required Twilio configuration")

            message = self.client.messages.create(
                body=message,
                from_=self.settings['from_number'],
                to=to
            )
            return True
        except Exception as e:
            print(f"Twilio SMS error: {str(e)}")
            raise

    async def _send_custom_sms(self, to: str, message: str) -> bool:
        """Send SMS using custom API"""
        try:
            if not all([self.api_url, self.api_key]):
                raise ValueError("Missing required custom API configuration")

            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
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

    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate phone number format"""
        # Add your phone number validation logic here
        return True