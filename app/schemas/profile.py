from pydantic import BaseModel
from typing import Optional

class ProfileUpdate(BaseModel):
    scheduling_url: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    welcome_message: Optional[str] = None
    company_logo: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    full_name: Optional[str] = None
    company: Optional[str] = None
    time_zone: Optional[str] = None

class Profile(ProfileUpdate):
    id: int
    user_id: int
    email: str

    class Config:
        from_attributes = True

class UserProfileSchema(BaseModel):
    full_name: Optional[str] = None
    company_logo: Optional[str] = None
    company: Optional[str] = None
    avatar_url: Optional[str] = None
    welcome_message: Optional[str] = None
    phone: Optional[str] = None
    time_zone: Optional[str] = None

    class Config:
        from_attributes = True
        
class TimezoneResponse(BaseModel):
    value: str
    label: str