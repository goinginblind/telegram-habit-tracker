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
        user_id=habit.user_id,
        type=habit.type,
        target=habit.target,
        start_date=habit.start_date or date.today()
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


@router.get("/habits/{habit_id}/streak")
def get_streak(user_id: int, habit_id: int, db: Session = Depends(get_db)):
    habit = get_habit(habit_id=habit_id, user_id=user_id, db=db)
    completions = get_completions_for_habit(user_id=user_id, habit_id=habit_id, db=db)

    if not completions:
        return 0

    # Extract dates where habit was completed
    completed_days = sorted({c.completed_at.date() for c in completions}, reverse=True)

    current_date = datetime.now(timezone.utc).date()
    streak = 0

    for date in completed_days:
        if habit.type in ("countable", "limit"):
            # Sum up completions for that day
            day_completions = [c for c in completions if c.completed_at.date() == date]
            total_value = sum(c.value or 0 for c in day_completions)

            if habit.type == "countable":
                if total_value < (habit.target or 1):
                    break  # not a completed day
            elif habit.type == "limit":
                if total_value >= (habit.target or 0):
                    break
        # Binary or passed checks
        if date == current_date:
            streak += 1
        else:
            expected = get_expected_date(date=current_date, repeat_type=habit.repeat_type)
            if date != expected:
                break
            streak += 1
            current_date = expected

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
    habits = get_habits_for_today(user_id=user_id, db=db)
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    summary = []

    for habit in habits:
        completions = db.query(models.HabitCompletion).filter(
            models.HabitCompletion.habit_id == habit.id,
            models.HabitCompletion.user_id == user_id,
            models.HabitCompletion.completed_at >= start_of_day,
            models.HabitCompletion.completed_at < end_of_day
        ).all()

        completed_today = False

        if habit.type == "binary":
            total_value = 1
            completed_today = bool(completions)

        elif habit.type == "countable":
            total_value = sum(c.value or 0 for c in completions)
            completed_today = total_value >= (habit.target or 1)

        elif habit.type == "limit":
            total_value = sum(c.value or 0 for c in completions)
            completed_today = total_value < (habit.target or 0)

        streak = get_streak(user_id, habit.id, db)

        summary.append({
            "id": habit.id,
            "name": habit.name,
            "repeat_type": habit.repeat_type,
            "type": habit.type,  # so frontend knows how to behave
            "current_value": total_value,
            "target": habit.target,
            "completed_today": completed_today,
            "streak": streak,
        })

    return summary