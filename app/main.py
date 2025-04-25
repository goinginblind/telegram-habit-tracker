from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app import models
from app.database import engine
from app.routes import habits, completions
from app.api.routes import api_router

app = FastAPI()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router)
app.include_router(completions.router)
app.include_router(habits.router)

templates = Jinja2Templates(directory="templates")

@app.get("/", include_in_schema=False)
async def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "API_BASE": "/api" 
    })

# DB tables
models.Base.metadata.create_all(bind=engine)

# index.html at "/"
@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("static/index.html")

# static files under /static
app.mount("/static", StaticFiles(directory="static"), name="static")
