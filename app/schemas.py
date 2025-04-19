from pydantic import BaseModel

class HabitCreate(BaseModel):
    name: str
    is_daily: bool = True


class Habit(BaseModel):
    id: int
    name: str
    is_daily: bool

    class Config:
        orm_mode = True