from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.routes.habits import get_db
from app import models, schemas
from app.models import Habit, HabitCompletion

from datetime import datetime, timezone, timedelta

from typing import List, Optional
from collections import defaultdict
import logging


router = APIRouter()

def create_completion(user_id: int, habit_id: int, db: Session, completed_at: Optional[datetime] = None):
    new_completion = models.HabitCompletion(
        habit_id=habit_id,
        completed_at=completed_at,
        user_id=user_id
    )

    db.add(new_completion)
    db.commit()
    db.refresh(new_completion)
    return new_completion

# For binary habits, allow check uncheck and db has 'completed' as the last time user checked it off
@router.post("/habits/{habit_id}/complete", response_model=schemas.CompletionRead)
def toggle_completion(
    habit_id: int,
    completion: schemas.CompletionCreate,
    db: Session = Depends(get_db),
):
    user_id = completion.user_id   # ← pull it from the body

    habit = (
        db.query(models.Habit)
          .filter(models.Habit.id == habit_id,
                  models.Habit.user_id == user_id)
          .first()
    )
    if habit is None:
        raise HTTPException(404, "Habit not found")
    if habit.type != "binary":
        raise HTTPException(400, "Toggle only supported for binary habits")

    today = datetime.now(timezone.utc).date()
    existing = (
      db.query(models.HabitCompletion)
        .filter(
          models.HabitCompletion.habit_id == habit_id,
          models.HabitCompletion.user_id == user_id,
          func.date(models.HabitCompletion.completed_at) == today
        ).first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return {"id": 0, "habit_id": habit_id, "user_id": user_id, "completed_at": None}
    else:
        return create_completion(user_id=user_id, habit_id=habit_id, db=db)


@router.get("/habits/{habit_id}/completions", response_model=List[schemas.CompletionRead])
def get_completions_for_habit(user_id: int, habit_id: int, db: Session = Depends(get_db)):
    completions = db.query(models.HabitCompletion).filter(
        models.HabitCompletion.habit_id == habit_id, 
        models.HabitCompletion.user_id == user_id
    ).all()

    return completions


@router.get("/habits/completion_calendar")
def completion_calendar(user_id: int, db: Session = Depends(get_db)):
    print(f"[DEBUG] Received raw user_id: {user_id}")
    # Step 1: Get all tracked habits
    habits = db.query(Habit).filter(
        Habit.user_id == user_id,
        Habit.tracked == True
    ).all()

    # Step 2: Get all completions for those habits
    completions = db.query(HabitCompletion).filter(
        HabitCompletion.user_id == user_id
    ).all()

    # Step 3: Group completions by date
    completions_by_day = defaultdict(set)  # date -> set of habit_ids completed
    for c in completions:
        completions_by_day[c.completed_at.date()].add(c.habit_id)

    # Step 4: For each date with a completion, count how many habits were expected that day
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
                total += 1  # Replace with your logic

        calendar[day.isoformat()] = {
            "completed": len(completions_by_day[day]),
            "total": total or 1
        }
    print(f"[LOG] Heatmap generated for {len(calendar)} days")

    return calendar