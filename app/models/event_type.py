from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from ..db.database import Base

class EventType(Base):
    __tablename__ = "event_types"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(String(255), nullable=True)
    duration = Column(Integer, nullable=False)  # duration in minutes
    color = Column(String(255), nullable=False, default="#3B82F6")  # default blue color
    is_active = Column(Boolean, default=True)
    locations = Column(JSON, nullable=True)  # Store location options (Google Meet, Zoom, etc.)
    questions = Column(JSON, nullable=True)  # Additional questions for bookings
    booking_rules = Column(JSON, nullable=True)  # Min notice, max notice, buffer time, etc.
    
    # Define relationships
    user = relationship("User", back_populates="event_types")
    events = relationship("Event", back_populates="event_type")