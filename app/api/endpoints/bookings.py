from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
from datetime import datetime, timedelta
from ...db.database import get_db
from ...models.event import Event
from ...models.event_type import EventType
from ...schemas.booking import BookingCreate, BookingResponse
from ...core.email.booking import send_booking_confirmation
from ...core.email.utils import generate_calendar_links

router = APIRouter()


@router.post("/bookings", response_model=BookingResponse)
async def create_booking(booking: BookingCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new booking"""
    # Get event type
    event_type = (
        db.query(EventType).filter(EventType.id == booking.event_type_id).first()
    )
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event type not found"
        )

    # Combine date and time
    date_str = f"{booking.date}T{booking.time}"
    start_time = datetime.fromisoformat(date_str)
    end_time = start_time + timedelta(minutes=event_type.duration)

    # Check if time slot is available
    existing_event = (
        db.query(Event)
        .filter(
            Event.event_type_id == event_type.id,
            Event.start_time < end_time,
            Event.end_time > start_time,
        )
        .first()
    )

    if existing_event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time slot is no longer available",
        )

    # Create event
    event_details = Event(
        user_id=event_type.user_id,
        event_type_id=event_type.id,
        title=event_type.name,
        start_time=start_time,
        end_time=end_time,
        description=booking.notes,
        attendee_name=booking.name,
        attendee_email=booking.email,
        location=booking.location,
        answers=booking.answers,
    )

    try:
        db.add(event_details)
        db.commit()
        db.refresh(event_details)

        calendar_links = generate_calendar_links(event_details)
        event_details.update(calendar_links)

        # Send confirmation emails
        await send_booking_confirmation(
            to_email=booking.email, event_details=event_details
        )

        return db_event
    except Exception as e:
        db.rollback()
        print(f"Failed to send confirmation email: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
