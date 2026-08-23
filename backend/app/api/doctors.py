"""Doctor module — patient list, patient summary, care plans."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import (
    AiInsight,
    Doctor,
    DoctorCarePlan,
    DoctorPatientRelationship,
    HealthMetric,
    MedicationLog,
    Medicine,
    User,
)
from app.api.deps import require_roles
from app.api.health import _values_for

router = APIRouter(prefix="/doctors", tags=["doctors"])


def _get_doctor(db: Session, user: User) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if doctor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor profile not found")
    return doctor


@router.get("/patients")
def my_patients(user: User = Depends(require_roles("doctor")), db: Session = Depends(get_db)):
    doctor = _get_doctor(db, user)
    rels = db.query(DoctorPatientRelationship).filter(
        DoctorPatientRelationship.doctor_id == doctor.id
    ).all()
    out = []
    for rel in rels:
        patient = db.get(User, rel.patient_user_id)
        if patient is None:
            continue
        p = patient.profile
        latest = (
            db.query(HealthMetric)
            .filter(HealthMetric.user_id == patient.id, HealthMetric.metric_type == "blood_pressure")
            .order_by(HealthMetric.measured_at.desc())
            .first()
        )
        bp = _values_for(latest) if latest else None
        logs = (
            db.query(MedicationLog)
            .join(Medicine, MedicationLog.medicine_id == Medicine.id)
            .filter(Medicine.user_id == patient.id)
            .all()
        )
        total = len(logs)
        taken = sum(1 for l in logs if l.status == "taken")
        adherence = round(taken / total * 100) if total else None
        out.append({
            "patient_id": patient.id,
            "name": patient.full_name,
            "age": _age(p.date_of_birth) if p and p.date_of_birth else None,
            "city": p.city if p else None,
            "latest_bp": bp,
            "adherence_rate": adherence,
        })
    return out


@router.get("/patients/{patient_id}/summary")
def patient_summary(patient_id: int, user: User = Depends(require_roles("doctor")),
                    db: Session = Depends(get_db)):
    doctor = _get_doctor(db, user)
    rel = db.query(DoctorPatientRelationship).filter(
        DoctorPatientRelationship.doctor_id == doctor.id,
        DoctorPatientRelationship.patient_user_id == patient_id,
    ).first()
    if rel is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Patient not assigned to you")
    patient = db.get(User, patient_id)
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")

    metrics = (
        db.query(HealthMetric)
        .filter(HealthMetric.user_id == patient_id)
        .order_by(HealthMetric.measured_at.desc())
        .limit(40)
        .all()
    )
    timeline = [
        {"metric_type": m.metric_type, "measured_at": m.measured_at.isoformat(), "values": _values_for(m)}
        for m in metrics
    ]
    meds = db.query(Medicine).filter(Medicine.user_id == patient_id, Medicine.active.is_(True)).all()
    insights = (
        db.query(AiInsight).filter(AiInsight.user_id == patient_id)
        .order_by(AiInsight.created_at.desc()).limit(10).all()
    )
    return {
        "patient": {"id": patient.id, "name": patient.full_name},
        "timeline": timeline,
        "medicines": [{"name": m.name, "dosage": m.dosage, "dosage_unit": m.dosage_unit,
                       "frequency": m.frequency} for m in meds],
        "insights": [{"title": i.title, "content": i.content, "severity": i.severity} for i in insights],
        "care_plans": [
            {"id": p.id, "title": p.title, "description": p.description, "status": p.status}
            for p in db.query(DoctorCarePlan).filter(DoctorCarePlan.elder_user_id == patient_id).all()
        ],
    }


class CarePlanIn(BaseModel):
    elder_user_id: int
    title: str
    description: str | None = None
    instructions: str | None = None


@router.post("/care-plans")
def create_care_plan(data: CarePlanIn, user: User = Depends(require_roles("doctor")),
                     db: Session = Depends(get_db)):
    doctor = _get_doctor(db, user)
    rel = db.query(DoctorPatientRelationship).filter(
        DoctorPatientRelationship.doctor_id == doctor.id,
        DoctorPatientRelationship.patient_user_id == data.elder_user_id,
    ).first()
    if rel is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Patient not assigned to you")
    plan = DoctorCarePlan(doctor_id=doctor.id, elder_user_id=data.elder_user_id,
                          title=data.title, description=data.description,
                          instructions=data.instructions)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return {"id": plan.id, "title": plan.title, "status": plan.status}


def _age(dob) -> int | None:
    try:
        today = datetime.utcnow().date()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return None
