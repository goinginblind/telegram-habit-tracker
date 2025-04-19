from pydantic import BaseModel

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