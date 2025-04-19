from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas, database

from typing import List

router = APIRouter()

# Get a DB session for the request
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
