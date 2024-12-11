from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..db.database import Base

class SMSSubscription(Base):
    __tablename__ = "sms_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider = Column(String(255))  # 'twilio', 'google', 'custom'
    account_sid = Column(String(255), nullable=True)
    auth_token = Column(String(255), nullable=True)
    from_number = Column(String(255), nullable=True)
    api_key = Column(String(255), nullable=True)
    api_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="sms_subscription")