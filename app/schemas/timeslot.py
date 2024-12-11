# schemas/timeslot.py
from typing import List
from pydantic import BaseModel
from datetime import datetime

class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    available: bool = True

class TimeSlotResponse(BaseModel):
    slots: List[TimeSlot]