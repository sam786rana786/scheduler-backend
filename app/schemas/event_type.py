from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class LocationType(str, Enum):
    GOOGLE_MEET = "google_meet"
    ZOOM = "zoom"
    IN_PERSON = "in_person"
    PHONE = "phone"
    CUSTOM = "custom"

class BookingRules(BaseModel):
    min_notice: Optional[int] = None  # minutes
    max_notice: Optional[int] = None  # minutes
    buffer_before: Optional[int] = None  # minutes
    buffer_after: Optional[int] = None  # minutes
    min_booking_notice: Optional[int] = None  # minutes
    max_bookings_per_day: Optional[int] = None

class Question(BaseModel):
    id: str
    type: str  # text, select, radio, etc.
    label: str
    required: bool = False
    options: Optional[List[str]] = None

class EventTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    duration: int
    color: str = "#3B82F6"
    is_active: bool = True
    locations: Optional[List[LocationType]] = None
    questions: Optional[List[Question]] = None
    booking_rules: Optional[BookingRules] = None

class EventTypeCreate(EventTypeBase):
    pass

class EventTypeUpdate(EventTypeBase):
    name: Optional[str] = None
    duration: Optional[int] = None

class EventType(EventTypeBase):
    id: int
    user_id: int
    slug: str

    host_name: Optional[str] = None
    host_email: Optional[str] = None

    class Config:
        from_attributes = True

class TimeSlot(BaseModel):
    start: str
    end: str

class AvailabilityResponse(BaseModel):
    event_type_id: int
    available_slots: List[TimeSlot]

class BookingRequest(BaseModel):
    start_time: str
    name: str
    email: EmailStr
    notes: Optional[str] = None
    location: Optional[str] = None
    answers: Optional[Dict[str, str]] = None