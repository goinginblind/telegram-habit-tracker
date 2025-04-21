from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.schemas import HabitUpdate, RepeatType
from app.routes.completions import get_completions_for_habit

from typing import List

from datetime import date, datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta


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
    habit = get_habit(habit_id=habit_id, user_id=user_id, db=db)
    completions = get_completions_for_habit(user_id=user_id, habit_id=habit_id, db=db)
    completions = sorted(completions, key=lambda c: c.completed_at, reverse=True)

    if not completions:
        return 0
    
    current_date, streak = datetime.now(timezone.utc).date(), 0

    for completion in completions:
        completion_day = completion.completed_at.date() 

        if completion_day == current_date:
            streak += 1
            current_date = get_expected_day(date=completion_day, repeat_type=habit.repeat_type)
        elif completion_day < current_date:
            break
    
    return streak
# This thing counts the expected day to get us our STREAKSSS (2 DAYS NO LEETCODE)
def get_expected_day(date: date, repeat_type: str) -> date:
    if repeat_type == RepeatType.DAILY:
        return date - timedelta(days=1)
    elif repeat_type == RepeatType.WEEKLY:
        return date - timedelta(days=7)
    elif repeat_type == RepeatType.BIWEEKLY:
        return date - timedelta(days=14)
    elif repeat_type == RepeatType.MONTHLY:
        return date - relativedelta(months=1)
    else:
        raise NotImplementedError("Custom is not yet supported :(")


# Gets todays habits
@router.get("/habits/today", response_model=List[schemas.Habit])
def get_habits_for_today(user_id: int, db: Session = Depends(get_db)):
    today = datetime.now(timezone.utc).date()

    habits = db.query(models.Habit).filter(
        models.Habit.tracked == True, 
        models.Habit.user_id == user_id
    ).all()

    habits_today = []
    for habit in habits:
        if habit.start_date > today:
            continue

        if habit.repeat_type == "daily":
            habits_today.append(habit)

        elif habit.repeat_type == "weekly":
            if (today - habit.start_date).days % 7 == 0:
                habits_today.append(habit)
        
        elif habit.repeat_type == "biweekly":
            if (today - habit.start_date).days % 14 == 0:
                habits_today.append(habit)
        
        elif habit.repeat_type == "monthly":
            if habit.start_date.day == today.day:
                habits_today.append(habit)
        
        elif habit.repeat_type == "custom":
            pass
    
    return habits_today

# Edit habits
@router.put("/habits/{habit_id}")
def update_habit(habit_id: int, habit_data: HabitUpdate, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(
        models.Habit.user_id == habit_data.user_id,
        models.Habit.id == habit_id
    ).first()

    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    for field, value in habit_data.model_dump(exclude_unset=True).items():
        setattr(habit, field, value)

    db.commit()
    db.refresh(habit)
    return habit

# Get one (user_id specific) habit
@router.get("/habits/{habit_id}", response_model=schemas.Habit)
def get_habit(habit_id: int, user_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter_by(id=habit_id, user_id=user_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit
