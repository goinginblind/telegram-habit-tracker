from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app import models
from app.database import engine
from app.routes import habits, completions

app = FastAPI()

# 1. Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Include API routes
app.include_router(completions.router)
app.include_router(habits.router)


# 3. Create DB tables
models.Base.metadata.create_all(bind=engine)

# 4. Serve index.html manually at "/"
@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("static/index.html")

# 5. Serve other static files under /static
app.mount("/static", StaticFiles(directory="static"), name="static")
