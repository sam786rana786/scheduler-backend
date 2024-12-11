from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..db.database import Base

class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    working_hours = Column(JSON)
    notification_settings = Column(JSON)
    email_settings = Column(JSON)
    sms_settings = Column(JSON)
    
    user = relationship("User", back_populates="settings")
