from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy import relationship

from datetime import datetime, timezone

from app.database import Base


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    is_daily = Column(Boolean, default=True)
    tracked = Column(Boolean, default=True)

    completions = relationship("HabitCompletion", back_populates="habit", cascade="all, delete")


class HabitCompletion(Base):
    __tablename__ = "habit_completions"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"))
    completed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)) 

    habit = relationship("Habit", back_populates="completions")