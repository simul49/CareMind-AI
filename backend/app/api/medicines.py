from datetime import datetime, date, time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Medicine, MedicationLog, MedicationSchedule, User
from app.api.deps import get_current_user
from app.schemas.common import DoseOut, MedicineIn, MedicineOut, ScheduleIn

router = APIRouter(prefix="/medicines", tags=["medicines"])


@router.get("", response_model=list[MedicineOut])
def list_medicines(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Medicine).filter(Medicine.user_id == user.id, Medicine.active.is_(True)).all()
    return rows


@router.post("", response_model=MedicineOut)
def create_medicine(data: MedicineIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m = Medicine(user_id=user.id, name=data.name, dosage=data.dosage, dosage_unit=data.dosage_unit,
                 frequency=data.frequency, instructions=data.instructions,
                 food_requirement=data.food_requirement, active=data.active, created_by=user.id)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.post("/{medicine_id}/schedules")
def add_schedule(medicine_id: int, data: ScheduleIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m = db.get(Medicine, medicine_id)
    if m is None or m.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medicine not found")
    try:
        hh, mm = data.scheduled_time.split(":")
        sched = MedicationSchedule(medicine_id=medicine_id, scheduled_time=time(int(hh), int(mm)),
                                   dosage_amount=data.dosage_amount, dosage_unit=data.dosage_unit)
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Time must be HH:MM")
    db.add(sched)
    db.commit()
    return {"status": "ok", "schedule_id": sched.id}


def _dose_out(db: Session, log: MedicationLog) -> DoseOut:
    sched = log.schedule
    return DoseOut(
        log_id=log.id,
        medicine_id=log.medicine_id,
        medicine_name=log.medicine.name,
        dosage=log.medicine.dosage,
        scheduled_time=sched.scheduled_time.strftime("%H:%M") if sched else "",
        scheduled_for=log.scheduled_for,
        status=log.status,
        taken_at=log.taken_at,
        instructions=log.medicine.instructions,
        food_requirement=log.medicine.food_requirement,
    )


@router.get("/today", response_model=list[DoseOut])
def today_doses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)
    logs = (
        db.query(MedicationLog)
        .join(Medicine)
        .filter(Medicine.user_id == user.id, MedicationLog.scheduled_for >= start,
                MedicationLog.scheduled_for <= end)
        .order_by(MedicationLog.scheduled_for.asc())
        .all()
    )
    return [_dose_out(db, l) for l in logs]


@router.post("/take/{log_id}", response_model=DoseOut)
def take_medicine(log_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log = db.get(MedicationLog, log_id)
    if log is None or log.medicine.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Log not found")
    log.status = "taken"
    log.taken_at = datetime.utcnow()
    db.commit()
    db.refresh(log)
    return _dose_out(db, log)


@router.post("/skip/{log_id}", response_model=DoseOut)
def skip_medicine(log_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log = db.get(MedicationLog, log_id)
    if log is None or log.medicine.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Log not found")
    log.status = "skipped"
    db.commit()
    db.refresh(log)
    return _dose_out(db, log)


@router.get("/adherence")
def adherence(days: int = 7, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    since = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    since -= timedelta(days=days - 1)
    logs = (
        db.query(MedicationLog)
        .join(Medicine)
        .filter(Medicine.user_id == user.id, MedicationLog.scheduled_for >= since)
        .all()
    )
    total = len(logs)
    taken = sum(1 for l in logs if l.status == "taken")
    rate = round(taken / total * 100) if total else 0
    return {"days": days, "total": total, "taken": taken, "adherence_rate": rate}
