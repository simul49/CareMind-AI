"""Caregiver module — Mom's Care Overview dashboard."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import (
    CareCircle,
    CareCircleMember,
    EmergencyEvent,
    HealthMetric,
    MedicationLog,
    Medicine,
    Post,
    User,
)
from app.api.deps import require_roles

router = APIRouter(prefix="/caregiver", tags=["caregiver"])


def _linked_elders(db: Session, user: User) -> list[User]:
    circle = (
        db.query(CareCircle)
        .join(CareCircleMember)
        .filter(CareCircleMember.user_id == user.id)
        .order_by(CareCircle.id.asc())
        .first()
    )
    if circle is None:
        return []
    members = db.query(CareCircleMember).filter(CareCircleMember.care_circle_id == circle.id).all()
    elders = []
    for m in members:
        u = db.get(User, m.user_id)
        if u and u.role and u.role.code == "elder":
            elders.append(u)
    return elders


@router.get("/overview")
def overview(user: User = Depends(require_roles("family", "caregiver")), db: Session = Depends(get_db)):
    elders = _linked_elders(db, user)
    result = {"elders": []}
    for elder in elders:
        p = elder.profile
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        # steps today
        steps = (
            db.query(HealthMetric)
            .filter(HealthMetric.user_id == elder.id, HealthMetric.metric_type == "activity",
                    HealthMetric.measured_at >= today_start)
            .all()
        )
        step_count = 0
        for m in steps:
            if m.activity:
                step_count += m.activity.steps or 0
        # medication adherence last 7 days
        since = today_start - timedelta(days=6)
        logs = (
            db.query(MedicationLog)
            .join(Medicine, MedicationLog.medicine_id == Medicine.id)
            .filter(Medicine.user_id == elder.id, MedicationLog.scheduled_for >= since)
            .all()
        )
        total = len(logs)
        taken = sum(1 for l in logs if l.status == "taken")
        adherence = round(taken / total * 100) if total else None
        # latest BP
        latest_bp = (
            db.query(HealthMetric)
            .filter(HealthMetric.user_id == elder.id, HealthMetric.metric_type == "blood_pressure")
            .order_by(HealthMetric.measured_at.desc())
            .first()
        )
        bp = None
        if latest_bp and latest_bp.blood_pressure:
            bp = {"systolic": latest_bp.blood_pressure.systolic,
                  "diastolic": latest_bp.blood_pressure.diastolic,
                  "measured_at": latest_bp.measured_at.isoformat()}
        # active emergency?
        active_event = (
            db.query(EmergencyEvent)
            .filter(EmergencyEvent.elder_user_id == elder.id, EmergencyEvent.status == "active")
            .first()
        )
        # recent posts
        recent_posts = (
            db.query(Post).filter(Post.author_id == elder.id)
            .order_by(Post.created_at.desc()).limit(3).all()
        )
        result["elders"].append({
            "id": elder.id,
            "name": elder.full_name,
            "age": _age(p.date_of_birth) if p and p.date_of_birth else None,
            "city": p.city if p else None,
            "steps_today": step_count,
            "adherence_rate": adherence,
            "latest_bp": bp,
            "has_active_emergency": active_event is not None,
            "last_post": recent_posts[0].content if recent_posts else None,
        })
    return result


def _age(dob) -> int | None:
    try:
        today = datetime.utcnow().date()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return None
