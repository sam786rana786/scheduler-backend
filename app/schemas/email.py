from pydantic import BaseModel, EmailStr
from datetime import datetime

class EmailTest(BaseModel):
    email: EmailStr

class EmailSettings(BaseModel):
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    from_email: EmailStr
    from_name: str