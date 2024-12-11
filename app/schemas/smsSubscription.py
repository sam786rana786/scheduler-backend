from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

class SMSSubscriptionBase(BaseModel):
    provider: Literal['twilio', 'google', 'custom']
    account_sid: Optional[str] = None
    auth_token: Optional[str] = None
    from_number: Optional[str] = None
    api_key: Optional[str] = None
    api_url: Optional[str] = None

class SMSSubscriptionCreate(SMSSubscriptionBase):
    pass

class SMSSubscriptionUpdate(SMSSubscriptionBase):
    is_active: Optional[bool] = None

class SMSSubscription(SMSSubscriptionBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True