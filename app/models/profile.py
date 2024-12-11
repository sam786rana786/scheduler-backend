from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..db.database import Base

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String(255))
    scheduling_url = Column(String(255), nullable=True)
    bio = Column(String(255), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    welcome_message = Column(String(255), nullable=True)
    company_logo = Column(String(255), nullable=True)
    phone = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    time_zone = Column(String(255), default="Asia/Kolkata")
    
    user = relationship("User", back_populates="profile")