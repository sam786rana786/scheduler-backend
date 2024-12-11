from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class UserMe(BaseModel):
    id: int
    email: str
    name: str | None
    phone: str | None
    is_active: bool
    valid: bool = True

    class Config:
        from_attributes = True