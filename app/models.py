from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLAlchemyEnum
from app.schemas import RepeatType, HabitType

from datetime import date, datetime, timezone

from app.database import Base


class Habit(Base):
    __tablename__ = "habits"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, index=True)
    name        = Column(String, index=True)
    tracked     = Column(Boolean, default=True)
    repeat_type = Column(SQLAlchemyEnum(RepeatType), default=RepeatType.DAILY)
    start_date  = Column(Date, default=date.today)
    type        = Column(SQLAlchemyEnum(HabitType), default=HabitType.BINARY)
    target      = Column(Integer, nullable=True)

    completions = relationship("HabitCompletion", back_populates="habit", cascade="all, delete")


class HabitCompletion(Base):
    __tablename__ = "habit_completions"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, index=True)
    habit_id     = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"))
    completed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    habit = relationship("Habit", back_populates="completions")