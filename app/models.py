from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class Habit(Base):
    __tablename__ = "habits"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    is_daily = Column(Boolean, default=True)
    tracked = Column(Boolean, default=True)