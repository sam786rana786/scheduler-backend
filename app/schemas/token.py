from pydantic import BaseModel

class Token(BaseModel):
    id: int
    user_id: int
    token: str

    class Config:
        from_attributes = True