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
    db_habit = models.Habit(
        name=habit.name, 
        repeat_type=habit.repeat_type, 
        tracked=habit.tracked,
        user_id=habit.user_id
    )
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit

# Get all of the habits
@router.get("/habits", response_model=List[schemas.Habit])
def get_habits(user_id: int, db: Session = Depends(get_db)):
    habits = db.query(models.Habit).filter(
        models.Habit.user_id == user_id
    ).all()
    return habits

# Get tracked habits only
@router.get("/habits/tracked", response_model=List[schemas.Habit])
def get_tracked_habits(user_id: int, db: Session = Depends(get_db)):
    habits = db.query(models.Habit).filter(
        models.Habit.tracked == True, 
        models.Habit.user_id == user_id
    ).all()
    return habits

# Delete a habit (hard and permanent)
@router.delete("/habits/{habit_id}", status_code=204)
def delete_habit(user_id: int, habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id, 
        models.Habit.user_id == user_id
    ).first()

    if habit is None:
        raise HTTPException(status_code=404, detail="Habit Not Found")
    
    db.delete(habit)
    db.commit()
    return

# Untrack a habit, so, basically a soft delete
@router.patch("/habits/{habit_id}/untrack")
def untrack_habit(user_id: int, habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id, 
        models.Habit.user_id == user_id
    ).first()

    if habit is None:
        raise HTTPException(status_code=404, detail="Habit Not Found")
    
    habit.tracked = False
    db.commit()
    db.refresh(habit)
    return

# Track a habit, bring back from the soft delete
@router.patch("/habits/{habit_id}/track")
def track_habit(user_id: int, habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id, 
        models.Habit.user_id == user_id
    ).first()

    if habit is None:
        raise HTTPException(status_code=404, detail="Habit Not Found")
    
    habit.tracked = True
    db.commit()
    db.refresh(habit)
    return

# Get habit streak
@router.get("/habits/{habit_id}/streak")
def get_streak(user_id: int, habit_id: int, db: Session = Depends(get_db)):
    completions = get_completions_for_habit(user_id=user_id, habit_id=habit_id, db=db)
    completions = sorted(completions, key=lambda c: c.completed_at, reverse=True)

    if not completions:
        return 0
    
    today, streak = datetime.now(timezone.utc).date(), 0

    for i, completion in enumerate(completions):
        completion_day = completion.completed_at.date()
        expected_date = today - timedelta(days=streak)

        if completion_day == expected_date:
            streak += 1
        elif completion_day < expected_date:
            break

    return streak

# NEED to add more types than just daily tho... fo shoo
@router.get("/habits/today")
def get_habits_for_today(user_id: int, db: Session = Depends(get_db)):
    today = datetime.now(timezone.utc).date()

    habits = db.query(models.Habit).filter(
        models.Habit.tracked == True, 
        models.Habit.user_id == user_id
    ).all()
    
    habits_today = []
    for habit in habits:
        if habit.repeat_type == "daily":
            habits_today.append(habit)
    
    return habits_today