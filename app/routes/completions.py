from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.routes.habits import get_db
from app import models, schemas

from datetime import datetime, timezone

from typing import List, Optional


router = APIRouter()

def create_completion(habit_id: int, db: Session, completed_at: Optional[datetime] = None):
    new_completion = models.HabitCompletion(
        habit_id=habit_id,
        completed_at=completed_at
    )

    db.add(new_completion)
    db.commit()
    db.refresh(new_completion)
    return new_completion


@router.post("/habits/{habit_id}/complete", response_model=schemas.CompletionRead)
def toggle_completion(habit_id: int, completion: schemas.CompletionCreate, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit Not Found")
    
    if habit.type != "binary":
        raise HTTPException(status_code=400, detail="This endpoint supports binary type only (for now)")
    
    today = datetime.now(timezone.utc).date()

    # So won't be situations where 'I have 3 daily habits, 
    # but 4 completions today, cool!' == no duplicates in case user misclicks!
    existing_completion = db.query(models.HabitCompletion).filter(
        models.HabitCompletion.habit_id == habit_id,
        func.date(models.HabitCompletion.completed_at) == today
    ).first()

    if existing_completion:
        db.delete(existing_completion)
        db.commit()
        raise HTTPException(status_code=200, detail="Habit unchecked for today")
    else:
        return create_completion(habit_id=habit_id, db=db)


@router.get("/habits/{habit_id}/completions", response_model=List[schemas.CompletionRead])
def get_completions_for_habit(user_id: int, habit_id: int, db: Session = Depends(get_db)):
    completions = db.query(models.HabitCompletion).filter(
        models.HabitCompletion.habit_id == habit_id, 
        models.HabitCompletion.user_id == user_id
    ).all()

    return completions