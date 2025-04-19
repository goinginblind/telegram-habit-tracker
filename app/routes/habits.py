from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

from typing import List

router = APIRouter()


@router.post("/habits")
def create_habit(habit: schemas.HabitCreate, db: Session = Depends(get_db)):
    db_habit = models.Habit(name=habit.name, is_daily=habit.is_daily, tracked=habit.tracked)
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit


@router.get("/habits", response_model=List[schemas.Habit])
def get_habits(db: Session = Depends(get_db)):
    habits = db.query(models.Habit).all()
    return habits


@router.get("/habits/tracked", response_model=List[schemas.Habit])
def get_tracked_habits(db: Session = Depends(get_db)):
    habits = db.query(models.Habit).filter(models.Habit.tracked == True).all()
    return habits


@router.delete("/habits/{habit_id}", status_code=204)
def delete_habit(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit Not Found")
    
    
    db.delete(habit)
    db.commit()
    return


@router.patch("/habits/{habit_id}/untrack")
def untrack_habit(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit Not Found")
    
    habit.tracked = False
    db.commit()
    db.refresh(habit)
    return