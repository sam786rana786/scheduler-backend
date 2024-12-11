from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
import string
import random
from ...db.database import get_db
from ...core.auth import get_current_user
from ...models.user import User
from ...models.event_type import EventType as EventTypeModel
from ...models.event import Event as EventModel
from ...models.settings import Settings as SettingsModel
from ...schemas.event_type import EventType, EventTypeCreate, EventTypeUpdate, AvailabilityResponse, TimeSlot, BookingRequest

router = APIRouter()

def generate_slug(name: str, user_id: int, db: Session) -> str:
    """Generate a unique slug for the event type"""
    base_slug = "-".join(name.lower().split())
    slug = base_slug
    
    while db.query(EventTypeModel).filter(EventTypeModel.slug == slug).first():
        # If slug exists, append random string
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        slug = f"{base_slug}-{random_string}"
    
    return slug

@router.get("/event-types", response_model=List[EventType])
async def get_event_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all event types for the current user"""
    return db.query(EventTypeModel).filter(
        EventTypeModel.user_id == current_user.id
    ).all()

@router.post("/event-types", response_model=EventType)
async def create_event_type(
    event_type: EventTypeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new event type"""
    slug = generate_slug(event_type.name, current_user.id, db)
    
    db_event_type = EventTypeModel(
        **event_type.dict(),
        user_id=current_user.id,
        slug=slug
    )
    
    try:
        db.add(db_event_type)
        db.commit()
        db.refresh(db_event_type)
        return db_event_type
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/event-types/{event_type_id}", response_model=EventType)
async def get_event_type(
    event_type_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific event type"""
    event_type = db.query(EventTypeModel).filter(
        EventTypeModel.id == event_type_id,
        EventTypeModel.user_id == current_user.id
    ).first()
    
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event type not found"
        )
    
    return event_type

@router.put("/event-types/{event_type_id}", response_model=EventType)
async def update_event_type(
    event_type_id: int,
    event_type_update: EventTypeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an event type"""
    event_type = db.query(EventTypeModel).filter(
        EventTypeModel.id == event_type_id,
        EventTypeModel.user_id == current_user.id
    ).first()
    
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event type not found"
        )
    
    # Update slug if name is changed
    update_data = event_type_update.dict(exclude_unset=True)
    if 'name' in update_data:
        update_data['slug'] = generate_slug(update_data['name'], current_user.id, db)
    
    for key, value in update_data.items():
        setattr(event_type, key, value)
    
    try:
        db.commit()
        db.refresh(event_type)
        return event_type
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/event-types/{event_type_id}")
async def delete_event_type(
    event_type_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an event type"""
    event_type = db.query(EventTypeModel).filter(
        EventTypeModel.id == event_type_id,
        EventTypeModel.user_id == current_user.id
    ).first()
    
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event type not found"
        )
    
    try:
        db.delete(event_type)
        db.commit()
        return {"message": "Event type deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.get("/event-types/{event_type_id}/availability", response_model=AvailabilityResponse)
async def get_event_type_availability(
    event_type_id: int,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get availability for an event type within a date range"""
    # Verify event type exists and belongs to user
    event_type = db.query(EventTypeModel).filter(
        EventTypeModel.id == event_type_id,
        EventTypeModel.user_id == current_user.id
    ).first()
    
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event type not found"
        )

    # Get user settings for working hours
    settings = db.query(SettingsModel).filter(
        SettingsModel.user_id == current_user.id
    ).first()
    
    if not settings or not settings.working_hours:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Working hours not configured"
        )

    # Get existing events within the date range
    existing_events = db.query(EventModel).filter(
        and_(
            EventModel.user_id == current_user.id,
            EventModel.start_time >= start_date,
            EventModel.end_time <= end_date
        )
    ).all()

    # Calculate available time slots
    available_slots: List[TimeSlot] = []
    current_date = start_date.date()
    
    while current_date <= end_date.date():
        day_name = current_date.strftime('%A').lower()
        day_settings = settings.working_hours.get(day_name)
        
        if day_settings and day_settings.get('enabled'):
            start_time = datetime.strptime(day_settings['start'], '%H:%M').time()
            end_time = datetime.strptime(day_settings['end'], '%H:%M').time()
            
            # Create time slots for the day
            current_time = datetime.combine(current_date, start_time)
            day_end = datetime.combine(current_date, end_time)
            
            while current_time + timedelta(minutes=event_type.duration) <= day_end:
                slot_end = current_time + timedelta(minutes=event_type.duration)
                
                # Check if slot conflicts with existing events
                is_available = not any(
                    event.start_time < slot_end and event.end_time > current_time
                    for event in existing_events
                )
                
                if is_available:
                    available_slots.append({
                        "start": current_time.isoformat(),
                        "end": slot_end.isoformat()
                    })
                
                current_time += timedelta(minutes=event_type.duration)
        
        current_date += timedelta(days=1)

    return {
        "event_type_id": event_type_id,
        "available_slots": available_slots
    }

@router.post("/event-types/{event_type_id}/book")
async def create_booking(
    event_type_id: int,
    booking: BookingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new booking for an event type"""
    # Verify event type exists and belongs to user
    event_type = db.query(EventTypeModel).filter(
        EventTypeModel.id == event_type_id,
        EventTypeModel.user_id == current_user.id
    ).first()
    
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event type not found"
        )

    # Verify time slot is available
    start_time = datetime.fromisoformat(booking.start_time)
    end_time = start_time + timedelta(minutes=event_type.duration)
    
    existing_event = db.query(EventModel).filter(
        and_(
            EventModel.user_id == current_user.id,
            EventModel.start_time < end_time,
            EventModel.end_time > start_time
        )
    ).first()
    
    if existing_event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time slot is not available"
        )

    # Create new event
    new_event = EventModel(
        user_id=current_user.id,
        event_type_id=event_type_id,
        title=f"{event_type.name} with {booking.name}",
        start_time=start_time,
        end_time=end_time,
        description=booking.notes,
        attendee_name=booking.name,
        attendee_email=booking.email,
        is_confirmed=True
    )

    try:
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return new_event
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )