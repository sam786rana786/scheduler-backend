from pydantic import BaseModel

class Token(BaseModel):
    id: int
    user_id: int
    token: str

    class Config:
        orm_mode = True