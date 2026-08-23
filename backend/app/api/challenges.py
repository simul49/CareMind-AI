"""Wellness challenges — a gentle daily goal for elders (Day 3)."""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, WellnessChallengeLog
from app.api.deps import get_current_user

router = APIRouter(prefix="/challenges", tags=["challenges"])

_CHALLENGES = [
    {"key": "walk", "badge": "Walk", "title": "Gentle 20-minute walk",
     "goal": "A slow stroll outside — even a short one counts.", "category": "activity"},
    {"key": "water", "badge": "Water", "title": "Drink 6 glasses of water",
     "goal": "Keep sipping through the day to stay hydrated.", "category": "hydration"},
    {"key": "stretch", "badge": "Stretch", "title": "Morning stretch routine",
     "goal": "Five gentle minutes to loosen up.", "category": "activity"},
    {"key": "mood", "badge": "Share", "title": "Share a happy moment",
     "goal": "Tell CareMind or your family one nice thing today.", "category": "mood"},
    {"key": "friends", "badge": "Call", "title": "Call someone you love",
     "goal": "A short call keeps hearts close.", "category": "social"},
    {"key": "sleep", "badge": "Sleep", "title": "Wind down by 9:30 PM",
     "goal": "Screens off and a warm drink before bed.", "category": "sleep"},
    {"key": "mind", "badge": "Breathe", "title": "5 minutes of slow breathing",
     "goal": "In through the nose, out slowly — feel the calm.", "category": "mindfulness"},
]


def _today_challenge() -> dict:
    return _CHALLENGES[date.today().toordinal() % len(_CHALLENGES)]


def _week_done(db: Session, user_id: int) -> int:
    week_start = datetime.combine(date.today() - timedelta(days=6), datetime.min.time())
    return (
        db.query(WellnessChallengeLog)
        .filter(WellnessChallengeLog.user_id == user_id, WellnessChallengeLog.completed_at >= week_start)
        .count()
    )


@router.get("/today")
def challenge_today(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ch = _today_challenge()
    today_start = datetime.combine(date.today(), datetime.min.time())
    done = (
        db.query(WellnessChallengeLog)
        .filter(
            WellnessChallengeLog.user_id == user.id,
            WellnessChallengeLog.challenge_key == ch["key"],
            WellnessChallengeLog.completed_at >= today_start,
        )
        .first()
        is not None
    )
    return {**ch, "done": done, "week_done": _week_done(db, user.id)}


@router.post("/today/complete")
def challenge_complete(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ch = _today_challenge()
    today_start = datetime.combine(date.today(), datetime.min.time())
    existing = (
        db.query(WellnessChallengeLog)
        .filter(
            WellnessChallengeLog.user_id == user.id,
            WellnessChallengeLog.challenge_key == ch["key"],
            WellnessChallengeLog.completed_at >= today_start,
        )
        .first()
    )
    if existing is None:
        db.add(WellnessChallengeLog(user_id=user.id, challenge_key=ch["key"]))
        db.commit()
    return {**ch, "done": True, "week_done": _week_done(db, user.id)}
