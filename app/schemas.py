from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from enum import Enum


class RepeatType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  


class HabitType(str, Enum):
    BINARY = "binary"
    COUNTABLE = "countable"
    LIMIT = "limit"


class HabitCreate(BaseModel):
    name: str
    repeat_type: RepeatType = RepeatType.DAILY
    start_date: Optional[date] = None
    tracked: bool = True
    user_id: int
    type: HabitType = HabitType.BINARY


class Habit(BaseModel):
    id: int
    user_id: int
    name: str
    repeat_type: RepeatType
    start_date: date
    tracked: bool
    type: HabitType
    target: Optional[int] = None

    model_config = {
        "from_attributes": True
    }

class HabitUpdate(BaseModel):
    name: Optional[int]
    repeat_type: Optional[str]
    start_day: Optional[date]
    tracked: Optional[bool]

    
    model_config = {
        "from_attributes": True
    }


class CompletionBase(BaseModel):
    user_id: int
    completed_at: Optional[datetime] = None


class CompletionCreate(CompletionBase):
    pass


class CompletionRead(CompletionBase):
    id: int
    habit_id: int

    model_config = {
        "from_attributes": True
    }