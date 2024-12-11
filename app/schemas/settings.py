from pydantic import BaseModel
from typing import Dict, Any

class Settings(BaseModel):
    working_hours: Dict[str, Any]
    notification_settings: Dict[str, Any]
    email_settings: Dict[str, Any]
    sms_settings: Dict[str, Any]
    id: int
    user_id: int

    class Config:
        from_attributes = True

class SettingsCreate(Settings):
    pass