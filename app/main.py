from fastapi import FastAPI
from app import models, database
from app.routes import habits
from app.routes import completions

app = FastAPI()

@app.get("/ping")
def ping():
    return {"message": "pong"}

models.Base.metadata.create_all(bind=database.engine)

app.include_router(habits.router)
app.include_router(completions.router)