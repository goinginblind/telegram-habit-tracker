from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models, schemas
from app.models import Habit, HabitCompletion

from datetime import datetime, timezone, timedelta

from typing import List, Optional
from collections import defaultdict
import logging


router = APIRouter()

def create_completion(user_id: int, habit_id: int, db: Session, completed_at: Optional[datetime] = None, value: Optional[int] = None):
    new_completion = models.HabitCompletion(
        habit_id=habit_id,
        completed_at=completed_at,
        user_id=user_id,
        value=value
    )

    db.add(new_completion)
    db.commit()
    db.refresh(new_completion)
    return new_completion


@router.post("/api/habits/{habit_id}/complete", response_model=schemas.CompletionRead)
def toggle_completion(
    habit_id: int,
    completion: schemas.CompletionCreate,
    db: Session = Depends(get_db),
):
    user_id = completion.user_id

    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == user_id
    ).first()

    if habit is None:
        raise HTTPException(404, "Habit not found")

    today = datetime.now(timezone.utc).date()

    # for binary it literally is toggle (upon toggling it either adds or deletes completion)
    if habit.type == "binary":
        existing = db.query(models.HabitCompletion).filter(
            models.HabitCompletion.habit_id == habit_id,
            models.HabitCompletion.user_id == user_id,
            func.date(models.HabitCompletion.completed_at) == today
        ).first()

        if existing:
            db.delete(existing)
            db.commit()
            return schemas.CompletionRead(
                id=0,
                habit_id=habit_id,
                user_id=user_id,
                completed_at=None
            )
        else:
            return create_completion(user_id=user_id, habit_id=habit_id, db=db)

    # countable / limit types 
    if completion.value is None:
        raise HTTPException(400, "Completion value is required for countable/limit habits")

    existing = db.query(models.HabitCompletion).filter(
        models.HabitCompletion.habit_id == habit_id,
        models.HabitCompletion.user_id == user_id,
        func.date(models.HabitCompletion.completed_at) == today
    ).first()

    if existing:
        new_value = (existing.value or 0) + completion.value
        if habit.type in ["limit", "countable"]:
            new_value = max(0, new_value)

        existing.value = new_value
        db.commit()
        db.refresh(existing)
        return existing
    else:
        if habit.type in ["limit", "countable"] and completion.value < 0:
            return schemas.CompletionRead(
                id=0,
                habit_id=habit_id,
                user_id=user_id,
                completed_at=None  # notice the dummy return (and its not even me)
            )

        return create_completion(
            user_id=user_id,
            habit_id=habit_id,
            db=db,
            completed_at=completion.completed_at,
            value=completion.value
        )


@router.get("/api/habits/{habit_id}/completions", response_model=List[schemas.CompletionRead])
def get_completions_for_habit(user_id: int, habit_id: int, db: Session = Depends(get_db)):
    completions = db.query(models.HabitCompletion).filter(
        models.HabitCompletion.habit_id == habit_id, 
        models.HabitCompletion.user_id == user_id
    ).all()

    return completions


# This WILL be used for a heatmap, but is not used now
@router.get("/habits/completion_calendar") 
def completion_calendar(user_id: int, db: Session = Depends(get_db)):
    print(f"[DEBUG] Received raw user_id: {user_id}")
    habits = db.query(Habit).filter(
        Habit.user_id == user_id,
        Habit.tracked == True
    ).all()

    completions = db.query(HabitCompletion).filter(
        HabitCompletion.user_id == user_id
    ).all()

    # completions are grouped by date
    completions_by_day = defaultdict(set)  # date -> set of habit_ids completed
    for c in completions:
        completions_by_day[c.completed_at.date()].add(c.habit_id)

    # compare set of completions for that day vs EXPECTED (so the thats where the 'heat' part comes from)
    calendar = {}

    for day in completions_by_day:
        total = 0
        for habit in habits:
            if habit.start_date > day:
                continue
            if habit.repeat_type == "daily":
                total += 1
            elif habit.repeat_type == "weekly" and day.weekday() == habit.start_date.weekday():
                total += 1
            elif habit.repeat_type == "biweekly":
                delta = (day - habit.start_date).days
                if delta % 14 == 0:
                    total += 1
            elif habit.repeat_type == "monthly" and day.day == habit.start_date.day:
                total += 1
            elif habit.repeat_type == "custom":
                total += 1  # a 'pass' is better? (is it?)

        calendar[day.isoformat()] = {
            "completed": len(completions_by_day[day]),
            "total": total or 1
        }
    print(f"[LOG] heatmap for {len(calendar)} days")

    return calendar