from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app import models, database
from app.routes import habits
from app.routes import completions


app = FastAPI()

# Behold, a LEGACY feature!
#@app.get("/ping")
#def ping():
#    return {"message": "pong"}

models.Base.metadata.create_all(bind=database.engine)

app.include_router(habits.router)
app.include_router(completions.router)
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)