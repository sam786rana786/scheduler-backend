from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class SMSTest(BaseModel):
    phone: str

class SMSSettings(BaseModel):
    provider: Literal['twilio', 'custom']
    account_sid: Optional[str] = None
    auth_token: Optional[str] = None
    from_number: Optional[str] = None
    api_key: Optional[str] = None
    api_url: Optional[str] = None