from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, users, clubs, club_applications, events, attendance, certificates, badges

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Campus-wide platform for college clubs, events, and student activities.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clubs.router)
app.include_router(club_applications.router)
app.include_router(events.router)
app.include_router(attendance.router)
app.include_router(certificates.router)
app.include_router(badges.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "version": "1.0.0"}
