import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes.auth import router as auth_router
from app.routes.profile import router as profile_router
from app.routes.resume import router as resume_router
from app.routes.resume_parsed import router as resume_parsed_router
from app.routes.jobs import router as jobs_router
from app.routes.matching import router as matching_router
from app.routes.skill_gap import router as skill_gap_router
from app.routes.cover_letter import router as cover_letter_router
from app.routes.interview import router as interview_router
from app.routes.career import router as career_router, assistant_router as career_assistant_router
from app.routes.applications import router as applications_router


# Load environment variables before anything reads them
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan event handler.
    Attempts to initialize tables safely on startup without blocking startup.
    """
    try:
        init_db()
    except Exception as exc:
        print(f"[Warning] Database tables could not be initialized at startup: {exc}")
    yield


app = FastAPI(
    title="AI Career Companion API",
    description="Backend service for AI Career Companion Agent for Internship Matching and Interview Preparation",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS origins
raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
)
allowed_origins = {
    origin.strip() for origin in raw_origins.split(",") if origin.strip()
}
allowed_origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})
allow_origin_regex = (
    r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
    if os.getenv("ENVIRONMENT", "development").lower() == "development"
    else None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins),
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(resume_router)
app.include_router(resume_router, prefix="/api")
app.include_router(resume_parsed_router)
app.include_router(jobs_router)

# Keep the legacy route structure for the existing UI while also exposing the
# /api namespace expected by the agent contract tests and external clients.
app.include_router(matching_router)
app.include_router(matching_router, prefix="/api")
app.include_router(skill_gap_router)
app.include_router(skill_gap_router, prefix="/api")
app.include_router(cover_letter_router)
app.include_router(cover_letter_router, prefix="/api")
app.include_router(interview_router)
app.include_router(interview_router, prefix="/api")
app.include_router(career_router)
app.include_router(career_router, prefix="/api")
app.include_router(career_assistant_router)
app.include_router(career_assistant_router, prefix="/api")
app.include_router(applications_router)
app.include_router(applications_router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "AI Career Companion API is running"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
