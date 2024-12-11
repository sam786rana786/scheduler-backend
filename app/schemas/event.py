# schemas/event.py
from pydantic import BaseModel, EmailStr, field_validator, Field
from datetime import datetime
from typing import Optional, Dict, Any, List

class EventBase(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    attendee_name: Optional[str] = None
    attendee_email: Optional[str] = None
    attendee_phone: Optional[str] = None
    location: Optional[str] = None
    answers: Optional[dict] = None
    is_confirmed: Optional[bool] = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EventCreate(EventBase):
    # Event creation only needs basic fields
    pass

class Event(EventBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class EventResponse(EventBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class EventList(BaseModel):
    items: List[EventResponse]
    total: int
    page: int
    pages: int

    @field_validator('items')
    def ensure_created_at(cls, v):
        for item in v:
            if not item.created_at:
                item.created_at = datetime.utcnow()
        return v

    class Config:
        from_attributes = True