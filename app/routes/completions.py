from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.routes.habits import get_db
from app import models, schemas

from datetime import datetime, timezone

from typing import List, Optional


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