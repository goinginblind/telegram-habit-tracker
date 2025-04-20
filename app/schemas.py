from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class RepeatType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  


class HabitCreate(BaseModel):
    name: str
    repeat_type: RepeatType = RepeatType.DAILY
    tracked: bool = True
    user_id: int


class Habit(BaseModel):
    id: int
    user_id: int
    name: str
    repeat_type: RepeatType
    tracked: bool
    type: Optional[str] = "binary"

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