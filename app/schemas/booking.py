from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Dict, Any

class BookingCreate(BaseModel):
    event_type_id: int
    date: str  # Format: YYYY-MM-DD
    time: str
    name: str
    email: EmailStr
    phone: str
    location: str
    notes: str = ""
    answers: Dict = {}

class BookingResponse(BaseModel):
    id: int
    event_type_id: int
    start_time: datetime
    end_time: datetime
    attendee_name: str
    attendee_email: str
    attendee_phone: str
    location: str
    description: Optional[str]
    answers: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True