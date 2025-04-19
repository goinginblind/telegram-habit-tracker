from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from routes.habits import get_db
import models, schemas
from datetime import datetime, timezone

router = APIRouter()

@router.post("/habits/{habit_id}/complete", response_model=schemas.CompletionRead)
def log_completion(habit_id: int, completion: schemas.CompletionCreate, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit Not Found")
    
    completed_at = completion.completed_at or datetime.now(timezone.utc)

    new_completion = models.HabitCompletion(
        habit_id=habit_id,
        completed_at=completed_at
    )
    
    db.add(new_completion)
    db.commit()
    db.refresh(new_completion)
    return new_completion