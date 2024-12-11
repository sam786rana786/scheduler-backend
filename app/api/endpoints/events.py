from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone, time
import pytz
from ...schemas.timeslot import TimeSlot
from ...db.database import get_db
from ...core.auth import get_current_user
from ...models.user import User
from ...models.profile import Profile
from ...models.settings import Settings
from ...models.event import Event as EventModel
from ...schemas.event import EventList, Event, EventCreate
from ...models.event_type import EventType as EventTypeModel  # Add this import
from ...schemas.event_type import EventType as EventTypeSchema  # If needed for response
from ...utils.notifications import send_notifications, send_cancellation_email
from sqlalchemy import or_

router = APIRouter()

@router.get("/events", response_model=EventList)
async def get_scheduled_events(
    status: Optional[str] = None,
    page: int = 1,
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.now()
    today_start = datetime.combine(now.date(), time.min)
    today_end = datetime.combine(now.date(), time.max)
    
    query = db.query(EventModel).filter(EventModel.user_id == current_user.id)
    
    # Add status filter
    if status:
        if status == "today":
            query = query.filter(
                EventModel.start_time >= today_start,
                EventModel.start_time <= today_end
            )
        elif status == "upcoming":
            query = query.filter(EventModel.start_time > today_end)
        elif status == "past":
            query = query.filter(EventModel.start_time < today_start)
    
    # Add search filter
    if q:
        query = query.filter(
            or_(
                EventModel.title.ilike(f"%{q}%"),
                EventModel.description.ilike(f"%{q}%")
            )
        )
    
    # Calculate pagination
    items_per_page = 10
    total = query.count()
    total_pages = (total + items_per_page - 1) // items_per_page
    
    # Add sorting and pagination
    query = query.order_by(EventModel.start_time.desc())
    query = query.offset((page - 1) * items_per_page).limit(items_per_page)
    
    events = query.all()
    
    return EventList(
        items=events,
        total=total,
        page=page,
        pages=total_pages
    )

@router.post("/events", response_model=Event)
async def create_event(
    event: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new event"""
    # Check for time slot availability
    existing_event = db.query(EventModel).filter(
        EventModel.user_id == current_user.id,
        EventModel.start_time < event.end_time,
        EventModel.end_time > event.start_time
    ).first()
    
    if existing_event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time slot is already booked"
        )
    
    db_event = EventModel(
        **event.dict(),
        user_id=current_user.id
    )
    
    try:
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/events/{event_id}", response_model=Event)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific event"""
    event = db.query(EventModel).filter(
        EventModel.id == event_id,
        EventModel.user_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return event

@router.put("/events/{event_id}", response_model=Event)
async def update_event(
    event_id: int,
    event_update: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an event"""
    event = db.query(EventModel).filter(
        EventModel.id == event_id,
        EventModel.user_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check for time slot availability if time is being updated
    if event_update.start_time != event.start_time or event_update.end_time != event.end_time:
        existing_event = db.query(EventModel).filter(
            EventModel.user_id == current_user.id,
            EventModel.id != event_id,
            EventModel.start_time < event_update.end_time,
            EventModel.end_time > event_update.start_time
        ).first()
        
        if existing_event:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time slot is already booked"
            )
    
    for key, value in event_update.dict(exclude_unset=True).items():
        setattr(event, key, value)
    
    try:
        db.commit()
        db.refresh(event)
        return event
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/events/{event_id}/cancel")
async def cancel_and_notify_event(
    event_id: int,
    reason: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel event, delete it, and notify user"""
    event = db.query(EventModel).filter(
        EventModel.id == event_id,
        EventModel.user_id == current_user.id
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Get settings for SMS notification
    settings = db.query(Settings).filter(Settings.user_id == current_user.id).first()
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    
    try:
        # Send notifications (email and optional SMS)
        notification_results = await send_notifications(
            event=event,
            user_settings=settings,
            reason=reason,
            profile=profile,
            attendee_email=event.attendee_email,
            attendee_phone=event.attendee_phone,
        )
        notification = {
            "message": "Event cancelled, deleted, and notifications sent",
            "notifications": notification_results
        }
        
        db.delete(event)
        db.commit()
        return notification
        # Delete the event
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel event: {str(e)}"
        )


@router.get("/timeslots", response_model=List[TimeSlot])
async def get_available_timeslots(
    start_date: datetime,
    end_date: datetime,
    event_type_id: int = Query(..., description="Event type ID is required"),  # Make required
    timezone: str = "Asia/Kolkata",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available time slots for a given date range based on event type"""
    try:
        # Use EventTypeModel instead of EventType
        event_type = db.query(EventTypeModel).filter(EventTypeModel.id == event_type_id).first()
        if not event_type:
            raise HTTPException(status_code=404, detail="Event type not found")
        
        # Duration in minutes from event type
        duration = event_type.duration
        
        # Generate time slots based on event type duration
        time_slots = []
        current_time = datetime.strptime("09:00", "%H:%M").time()
        end_time = datetime.strptime("17:00", "%H:%M").time()
        interval = timedelta(minutes=duration)
        
        current_date = start_date
        while current_date <= end_date:
            slot_time = current_time
            while slot_time < end_time:
                slot_start = datetime.combine(current_date.date(), slot_time)
                slot_end = slot_start + interval
                
                # Check for conflicts
                is_available = not db.query(EventModel).filter(
                    EventModel.user_id == current_user.id,
                    EventModel.start_time < slot_end,
                    EventModel.end_time > slot_start
                ).first()
                
                if is_available:
                    time_slots.append(TimeSlot(
                        start_time=slot_start,
                        end_time=slot_end,
                        available=True
                    ))
                    
                slot_time = (datetime.combine(current_date.date(), slot_time) + interval).time()
            current_date += timedelta(days=1)
        
        return time_slots
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating time slots: {str(e)}"
        )
