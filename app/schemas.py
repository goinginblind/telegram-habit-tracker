from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class HabitCreate(BaseModel):
    name: str
    is_daily: bool = True
    tracked: bool = True


class Habit(BaseModel):
    id: int
    name: str
    is_daily: bool
    tracked: bool

    class Config:
        orm_mode = True


class CompletionBase(BaseModel):
    completed_at: Optional[datetime] = None


class CompletionCreate(CompletionBase):
    pass


class CompletionRead(CompletionBase):
    id: int
    habit_id: int

    class Config:
        orm_mode = True