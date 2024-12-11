from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Any, List, Optional
from ...db.database import get_db
import re
from ...models.event_type import EventType
from ...models.event import Event
from ...models.user import User
from ...models.profile import Profile
from ...models.settings import Settings
from ...schemas.profile import UserProfileSchema
from ...schemas.event_type import EventType as EventTypeSchema
from ...schemas.booking import BookingCreate, BookingResponse
from ...utils.notifications import send_booking_confirmation_email, send_booking_confirmation_sms

router = APIRouter()

def validate_date_format(date_str: str) -> bool:
    """Validate date string format (YYYY-MM-DD)"""
    pattern = r'^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$'
    return bool(re.match(pattern, date_str))

def validate_time_format(time_str: str) -> bool:
    """Validate time string format (HH:MM)"""
    pattern = r'^(?:[01]\d|2[0-3]):[0-5]\d$'
    return bool(re.match(pattern, time_str))


@router.get("/public/event-types/{identifier}", response_model=EventTypeSchema)
async def get_public_event_type(
    identifier: str,
    by_id: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get public event type details by either slug or ID
    
    Args:
        identifier: Either the slug or ID of the event type
        by_id: If True, treat identifier as an ID; if False, treat it as a slug
    """
    # Build the base query with necessary joins
    query = db.query(EventType, User, Profile).join(
        User, EventType.user_id == User.id
    ).join(
        Profile, User.id == Profile.user_id
    )
    
    # Apply the appropriate filter based on whether we're looking up by ID or slug
    if by_id:
        try:
            event_type_id = int(identifier)
            event_type = query.filter(
                EventType.id == event_type_id,
                EventType.is_active == True
            ).first()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid event type ID"
            )
    else:
        event_type = query.filter(
            EventType.slug == identifier,
            EventType.is_active == True
        ).first()

    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event type not found"
        )

    # Format the response data
    response_data = {
        # Event type fields
        "id": event_type[0].id,
        "user_id": event_type[0].user_id,
        "name": event_type[0].name,
        "slug": event_type[0].slug,
        "description": event_type[0].description,
        "duration": event_type[0].duration,
        "color": event_type[0].color,
        "is_active": event_type[0].is_active,
        "locations": event_type[0].locations,
        "questions": event_type[0].questions,
        "booking_rules": event_type[0].booking_rules,
        # Host information
        "host_name": event_type[2].full_name,
        "host_email": event_type[1].email
    }

    return EventTypeSchema(**response_data)


@router.get("/public/availability/{event_type_id}")
async def get_public_availability(
    event_type_id: int,
    date: str,
    db: Session = Depends(get_db)
):
    """Get available time slots for a specific date"""
    # Verify event type exists and is active
    event_type = db.query(EventType).filter(
        EventType.id == event_type_id,
        EventType.is_active == True
    ).first()

    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event type not found"
        )

    try:
        # Parse the date
        booking_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    # Get the user's settings
    user_settings = db.query(Settings).filter(Settings.user_id == event_type.user_id).first()

    if not user_settings or not user_settings.working_hours:
        return {"available_slots": []}

    # Get day of week
    day_of_week = booking_date.strftime("%A").lower()
    day_schedule = user_settings.working_hours.get(day_of_week)

    if not day_schedule or not day_schedule.get("enabled"):
        return {"available_slots": []}

    # Generate time slots based on working hours
    start_time = datetime.strptime(day_schedule["start"], "%H:%M").time()
    end_time = datetime.strptime(day_schedule["end"], "%H:%M").time()
    
    slots = []
    current_time = datetime.combine(booking_date, start_time)
    end_datetime = datetime.combine(booking_date, end_time)

    while current_time + timedelta(minutes=event_type.duration) <= end_datetime:
        # Check if slot is already booked
        is_available = not db.query(Event).filter(
            Event.event_type_id == event_type_id,
            Event.start_time < current_time + timedelta(minutes=event_type.duration),
            Event.end_time > current_time
        ).first()

        if is_available:
            slots.append(current_time.strftime("%H:%M"))

        current_time += timedelta(minutes=event_type.duration)  # event-type duration

    return {"available_slots": slots}

@router.post("/public/bookings", response_model=BookingResponse)
async def create_public_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db)
):
    """Create a public booking"""
    try:
        # Get event type and host user
        event_type = db.query(EventType).filter(EventType.id == booking.event_type_id).first()
        if not event_type:
            raise HTTPException(status_code=404, detail="Event type not found")

        host_user = db.query(User).filter(User.id == event_type.user_id).first()
        if not host_user:
            raise HTTPException(status_code=404, detail="Host user not found")
            
        # Combine date and time
        datetime_str = f"{booking.date}T{booking.time}"
        try:
            start_time = datetime.fromisoformat(datetime_str)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date or time format. Expected YYYY-MM-DD and HH:MM"
            )

        end_time = start_time + timedelta(minutes=event_type.duration)

        # Create booking
        db_booking = Event(
            user_id=host_user.id,
            event_type_id=booking.event_type_id,
            title=event_type.name,
            start_time=start_time,
            end_time=end_time,
            description=booking.notes or f"Slot booked by {booking.name}",
            attendee_name=booking.name,
            attendee_email=booking.email,
            attendee_phone=booking.phone,
            location=booking.location,
            answers=booking.answers,
            is_confirmed=True
        )
        
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)

        # Get host settings for notifications
        host_settings = db.query(Settings).filter(Settings.user_id == host_user.id).first()
        host_profile = db.query(Profile).filter(Profile.user_id == host_user.id).first()

        # Send email notifications
        if host_settings and host_settings.email_settings:
            try:
                # Send to attendee
                await send_booking_confirmation_email(
                    to_email=booking.email,
                    event_title=event_type.name,
                    event_time=start_time,
                    attendee_name=booking.name,
                    host_name=host_profile.full_name,
                    location=booking.location,
                    email_settings=host_settings.email_settings,
                )
                
                # Send to host
                await send_booking_confirmation_email(
                    to_email=host_user.email,
                    event_title=f"New Booking: {event_type.name}",
                    event_time=start_time,
                    attendee_name=booking.name,
                    host_name=host_profile.full_name,
                    location=booking.location,
                    email_settings=host_settings.email_settings
                )
            except Exception as e:
                print(f"Failed to send booking confirmation email: {str(e)}")

        # Send SMS notifications
        if (host_settings and 
            host_settings.sms_settings and 
            host_settings.notification_settings.get('sms', {}).get('enabled') and
            booking.phone):
            try:
                # Send to attendee
                await send_booking_confirmation_sms(
                    to_phone=booking.phone,
                    event_title=event_type.name,
                    event_time=start_time,
                    sms_settings=host_settings.sms_settings
                )
                
                # Send to host if phone available
                if host_profile.phone:
                    await send_booking_confirmation_sms(
                        to_phone=host_profile.phone,
                        event_title=f"New Booking: {event_type.name}",
                        event_time=start_time,
                        sms_settings=host_settings.sms_settings
                    )
            except Exception as e:
                print(f"Failed to send booking confirmation SMS: {str(e)}")

        return db_booking

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/public/bookings/{booking_id}", response_model=BookingResponse)
async def get_public_booking(
    booking_id: int,
    db: Session = Depends(get_db)
):
    """Get public booking details"""
    booking = db.query(Event).filter(Event.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    return booking

@router.get("/public/profile/{user_id}", response_model=UserProfileSchema)
async def get_user_profile(
    user_id: int, 
    db: Session = Depends(get_db)
    ) -> Any:
    # Query the user profile based on the user_id
    user_profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Format the response data
    response_data = {
        "full_name": user_profile.full_name,
        "company_logo": user_profile.company_logo,
        "company": user_profile.company,
        "avatar_url": user_profile.avatar_url,
        "welcome_message": user_profile.welcome_message,
        "phone": user_profile.phone,
        "time_zone": user_profile.time_zone
    }
    
    return response_data