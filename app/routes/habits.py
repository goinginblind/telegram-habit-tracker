from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routes.completions import get_completions_for_habit

from typing import List

from datetime import datetime, timedelta, timezone


router = APIRouter()

# Create a new habit
@router.post("/habits")
def create_habit(habit: schemas.HabitCreate, db: Session = Depends(get_db)):
    db_habit = models.Habit(name=habit.name, is_daily=habit.is_daily, tracked=habit.tracked)
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit

# Get all of the habits
@router.get("/habits", response_model=List[schemas.Habit])
def get_habits(db: Session = Depends(get_db)):
    habits = db.query(models.Habit).all()
    return habits

# Get tracked habits only
@router.get("/habits/tracked", response_model=List[schemas.Habit])
def get_tracked_habits(db: Session = Depends(get_db)):
    habits = db.query(models.Habit).filter(models.Habit.tracked == True).all()
    return habits

# Delete a habit (hard and permanent)
@router.delete("/habits/{habit_id}", status_code=204)
def delete_habit(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit Not Found")
    
    
    db.delete(habit)
    db.commit()
    return

# Untrack a habit, so, basically a soft delete
@router.patch("/habits/{habit_id}/untrack")
def untrack_habit(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit Not Found")
    
    habit.tracked = False
    db.commit()
    db.refresh(habit)
    return

# Track a habit, bring back from the soft delete
@router.patch("/habits/{habit_id}/track")
def track_habit(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit Not Found")
    
    habit.tracked = True
    db.commit()
    db.refresh(habit)
    return

# Get habit streak
@router.get("/habits/{habit_id}/streak")
def get_streak(habit_id: int, db: Session = Depends(get_db)):
    completions = get_completions_for_habit(habit_id=habit_id, db=db)
    completions = sorted(completions, key=lambda c: c.completed_at, reverse=True)

    if not completions:
        return 0
    
    today, streak = datetime.now(timezone.utc).date(), 0
    day_ptr = today

    for completion in completions:
        completion_day = completion.completed_at.date()

        if completion_day == day_ptr:
            streak += 1
            day_ptr -= timedelta(days=1)
        elif completion_day < day_ptr:
            break

    return streak
