from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from enum import Enum


class RepeatType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  # Not yet supported but l8r (in a week) will allow custom weekdays  


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
    type: HabitType
    target: Optional[int] = None


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
    user_id: int
    id: int
    name: Optional[str]
    repeat_type: Optional[str]
    start_date: Optional[date]
    tracked: Optional[bool]
    target: Optional[int]
    type: Optional[HabitType]

    
    model_config = {
        "from_attributes": True
    }


class CompletionBase(BaseModel):
    user_id: int
    completed_at: Optional[datetime] = None
    value: Optional[int] = None


class CompletionCreate(CompletionBase):  # simply inherist from base so that's why its empty
    pass


class CompletionRead(CompletionBase):
    id: int
    habit_id: int

    model_config = {
        "from_attributes": True
    }