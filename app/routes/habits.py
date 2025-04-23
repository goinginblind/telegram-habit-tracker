from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.schemas import HabitUpdate, RepeatType
from app.routes.completions import get_completions_for_habit

from typing import Dict, List

from datetime import date, datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from calendar import monthrange

from app.logger import logger


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
    completed_today = False
    last_completed_date = None

    for completion in completions:
        completion_day = completion.completed_at.date()

        if completion_day == current_date:
            streak += 1
            completed_today = True
            continue  # Exit early once we see completion for today
        elif completion_day < current_date:
            # Adjust target day logic based on repeat_type
            if habit.repeat_type == "daily":
                # Reset streak if habit wasn't completed today
                if (current_date - completion_day).days > 1:
                    streak = 0
                    break
            elif habit.repeat_type == "weekly":
                # Reset streak if habit wasn't completed on the specific target day of the week
                if completion_day.weekday() != current_date.weekday():
                    streak = 0
                    break
            # Add logic for other repeat types as needed
            current_date = get_expected_date(date=completion_day, repeat_type=habit.repeat_type)
            streak += 1
            last_completed_date = completion_day

    # Reset streak if habit wasn't completed for the target day
    if not completed_today and streak == 0:
        return 0  # Habit wasn't completed on the target day, reset streak

    return streak


# This thing counts the expected day to get us our STREAKSSS (2 DAYS NO LEETCODE)
def get_expected_date(date: date, repeat_type: str) -> date:
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

    today = datetime.now(timezone.utc).date()
    habits = db.query(models.Habit).filter(
        models.Habit.tracked == True,
        models.Habit.user_id == user_id
    ).all()

    habits_today = []
    for habit in habits:
        logger.debug(f"Habit {habit.name} — start: {habit.start_date}, today: {today}, repeat_type: {habit.repeat_type}")
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
            start_day = habit.start_date.day
            last_day_current_month = monthrange(today.year, today.month)[1]
            # so if a habits start day is the last day of the month (i.e. 31st) and curr month has less days, 
            # append todays habits with this habit if today is the last day of the month 
            if start_day >= 28:
                if today.day == last_day_current_month:
                    habits_today.append(habit)
            else:
                if today.day == start_day:
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

# Get ttodays progress for da wheel
@router.get("/progress/today", response_model=Dict[str, float])
def get_todays_progress(user_id: int, db: Session = Depends(get_db)):
    habits = get_habits_for_today(user_id=user_id, db=db)
    completions_count = 0
    total_count = len(habits)
    today = datetime.now().date()

    for habit in habits:
        completions = get_completions_for_habit(user_id=user_id, habit_id=habit.id, db=db)
        if any(c.completed_at.date() == today for c in completions):
            completions_count += 1
    
    return {"progress": completions_count / total_count * 100 if total_count > 0 else 0}


# Gets todays summary to lessen load from the frontend i guess
@router.get("/habits/today/summary")
def get_today_summary(user_id: int, db: Session = Depends(get_db)):

    # all habits active today
    habits = get_habits_for_today(user_id=user_id, db=db)

    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    completions_today = db.query(models.HabitCompletion.habit_id).filter(
        models.HabitCompletion.user_id == user_id,
        models.HabitCompletion.completed_at >= start_of_day,
        models.HabitCompletion.completed_at < end_of_day
    ).all()
    completed_today_ids = {row.habit_id for row in completions_today}

    # Habits streaks
    summary = []
    for habit in habits:
        streak = get_streak(user_id, habit.id, db)
        summary.append({
            "id": habit.id,
            "name": habit.name,
            "repeat_type": habit.repeat_type,
            "completed_today": habit.id in completed_today_ids,
            "streak": streak,
        })

    return summary