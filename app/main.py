from fastapi import FastAPI
from app import models, database
from app.routes import habits

app = FastAPI()

@app.get("/ping")
def ping():
    return {"message": "pong"}

models.Base.metadata.create_all(bind=database.engine)

app.include_router(habits.router)