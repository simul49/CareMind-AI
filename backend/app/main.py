from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.api import auth, users, health, medicines, ai, emergency, care, doctors, caregivers, reports
from app.services.seed import seed_all

app = FastAPI(
    title=settings.APP_NAME,
    description="Private AI-powered digital care ecosystem — Older Adults + Family + Doctor + AI",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_all()


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "docs": "/docs",
        "status": "running",
        "demo": "Hackathon demo build — Day 1 foundation",
    }


for router in (
    auth.router,
    users.router,
    health.router,
    medicines.router,
    ai.router,
    emergency.router,
    care.router,
    doctors.router,
    caregivers.router,
    reports.router,
):
    app.include_router(router)
