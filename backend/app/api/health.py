from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import (
    ActivityRecord,
    BloodPressureRecord,
    GlucoseRecord,
    HealthMetric,
    HeartRateRecord,
    MoodRecord,
    SleepRecord,
    User,
    WeightRecord,
)
from app.api.deps import get_current_user
from app.schemas.common import (
    ActivityIn,
    BloodPressureIn,
    GlucoseIn,
    HeartRateIn,
    MetricOut,
    MoodIn,
    SleepIn,
    WeightIn,
)

router = APIRouter(prefix="/health", tags=["health"])

DETAIL_MODELS = {
    "blood_pressure": (BloodPressureRecord, "systolic"),
    "heart_rate": (HeartRateRecord, "bpm"),
    "glucose": (GlucoseRecord, "value_mg_dl"),
    "weight": (WeightRecord, "kg"),
}


def _values_for(metric: HealthMetric) -> dict:
    bp = metric.blood_pressure
    hr = metric.heart_rate
    glu = metric.glucose
    w = metric.weight
    sl = metric.sleep
    act = metric.activity
    mo = metric.mood
    if bp:
        return {"systolic": bp.systolic, "diastolic": bp.diastolic, "pulse": bp.pulse}
    if hr:
        return {"bpm": hr.bpm}
    if glu:
        return {"value_mg_dl": glu.value_mg_dl, "context": glu.measurement_context}
    if w:
        return {"kg": w.kg}
    if sl:
        return {"sleep_hours": sl.sleep_hours, "quality": sl.quality}
    if act:
        return {
            "activity_type": act.activity_type,
            "steps": act.steps,
            "duration_minutes": act.duration_minutes,
            "distance_km": act.distance_km,
            "calories": act.calories,
            "note": act.note,
        }
    if mo:
        return {"mood_level": mo.mood_level, "note": mo.note}
    return {}


def _add_metric(db: Session, user_id: int, metric_type: str, measured_at: datetime | None, detail) -> MetricOut:
    m = HealthMetric(user_id=user_id, metric_type=metric_type, measured_at=measured_at or datetime.utcnow())
    db.add(m)
    db.flush()
    detail.metric_id = m.id
    db.add(detail)
    db.commit()
    db.refresh(m)
    return MetricOut(id=m.id, metric_type=m.metric_type, measured_at=m.measured_at, values=_values_for(m))


@router.post("/blood-pressure", response_model=MetricOut)
def record_bp(data: BloodPressureIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not (50 <= data.systolic <= 260 and 30 <= data.diastolic <= 150):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Out-of-range blood pressure values")
    return _add_metric(db, user.id, "blood_pressure", data.measured_at,
                       BloodPressureRecord(systolic=data.systolic, diastolic=data.diastolic, pulse=data.pulse))


@router.post("/heart-rate", response_model=MetricOut)
def record_hr(data: HeartRateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _add_metric(db, user.id, "heart_rate", data.measured_at, HeartRateRecord(bpm=data.bpm))


@router.post("/glucose", response_model=MetricOut)
def record_glucose(data: GlucoseIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _add_metric(db, user.id, "glucose", data.measured_at,
                       GlucoseRecord(value_mg_dl=data.value_mg_dl, measurement_context=data.measurement_context))


@router.post("/weight", response_model=MetricOut)
def record_weight(data: WeightIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _add_metric(db, user.id, "weight", data.measured_at, WeightRecord(kg=data.kg))


@router.post("/activity", response_model=MetricOut)
def record_activity(data: ActivityIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _add_metric(db, user.id, "activity", data.measured_at,
                       ActivityRecord(activity_type=data.activity_type, steps=data.steps,
                                      duration_minutes=data.duration_minutes, distance_km=data.distance_km,
                                      calories=data.calories, note=data.note))


@router.post("/sleep", response_model=MetricOut)
def record_sleep(data: SleepIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _add_metric(db, user.id, "sleep", data.measured_at,
                       SleepRecord(sleep_hours=data.sleep_hours, quality=data.quality,
                                   start_time=data.start_time, end_time=data.end_time))


@router.post("/mood", response_model=MetricOut)
def record_mood(data: MoodIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _add_metric(db, user.id, "mood", data.measured_at,
                       MoodRecord(mood_level=data.mood_level, note=data.note))


@router.get("/timeline", response_model=list[MetricOut])
def timeline(days: int = 14, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(HealthMetric)
        .filter(HealthMetric.user_id == user.id, HealthMetric.measured_at >= since)
        .order_by(HealthMetric.measured_at.desc())
        .all()
    )
    return [MetricOut(id=m.id, metric_type=m.metric_type, measured_at=m.measured_at, values=_values_for(m)) for m in rows]


@router.get("/today")
def today_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        db.query(HealthMetric)
        .filter(HealthMetric.user_id == user.id, HealthMetric.measured_at >= start)
        .all()
    )
    summary = {"blood_pressure": None, "heart_rate": None, "glucose": None, "weight": None,
               "steps": 0, "sleep_hours": None, "mood": None, "activity_count": 0}
    for m in rows:
        vals = _values_for(m)
        t = m.metric_type
        if t == "blood_pressure" and summary["blood_pressure"] is None:
            summary["blood_pressure"] = vals
        elif t == "heart_rate" and summary["heart_rate"] is None:
            summary["heart_rate"] = vals
        elif t == "glucose" and summary["glucose"] is None:
            summary["glucose"] = vals
        elif t == "weight":
            summary["weight"] = vals
        elif t == "activity":
            summary["steps"] += vals.get("steps") or 0
            summary["activity_count"] += 1
        elif t == "sleep" and summary["sleep_hours"] is None:
            summary["sleep_hours"] = vals.get("sleep_hours")
        elif t == "mood":
            summary["mood"] = vals
    return summary


@router.get("/trends/{metric_type}")
def trends(metric_type: str, days: int = 14, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(HealthMetric)
        .filter(HealthMetric.user_id == user.id, HealthMetric.metric_type == metric_type,
                HealthMetric.measured_at >= since)
        .order_by(HealthMetric.measured_at.asc())
        .all()
    )
    points = []
    for m in rows:
        vals = _values_for(m)
        if metric_type == "blood_pressure":
            points.append({"measured_at": m.measured_at.isoformat(),
                           "systolic": vals.get("systolic"), "diastolic": vals.get("diastolic")})
        elif vals:
            points.append({"measured_at": m.measured_at.isoformat(), "value": list(vals.values())[0]})
    return {"metric_type": metric_type, "points": points}
