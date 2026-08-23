from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import EmergencyContact, EmergencyEvent, EmergencyLog, User
from app.api.deps import get_current_user
from app.services import emergency_service
from app.schemas.common import EmergencyContactIn, EmergencyTriggerIn

router = APIRouter(prefix="/emergency", tags=["emergency"])


class ResolveIn(BaseModel):
    summary: str | None = None


@router.post("/trigger")
def trigger(data: EmergencyTriggerIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return emergency_service.trigger_sos(
        db, user, data.trigger_type, data.location_label, data.location_lat, data.location_lng
    )


@router.get("/events")
def list_events(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(EmergencyEvent)
        .filter(EmergencyEvent.elder_user_id == user.id)
        .order_by(EmergencyEvent.started_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": e.id,
            "trigger_type": e.trigger_type,
            "status": e.status,
            "location_label": e.location_label,
            "started_at": e.started_at.isoformat(),
            "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
            "summary": e.summary,
        }
        for e in rows
    ]


@router.post("/events/{event_id}/resolve")
def resolve(event_id: int, data: ResolveIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.get(EmergencyEvent, event_id)
    if event is None or event.elder_user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")
    return emergency_service.resolve_event(db, event, data.summary)


@router.get("/contacts")
def list_contacts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(EmergencyContact).filter(EmergencyContact.elder_user_id == user.id).all()
    return [
        {"id": c.id, "name": c.name, "relationship_type": c.relationship_type,
         "phone": c.phone, "is_primary": c.is_primary}
        for c in rows
    ]


@router.post("/contacts")
def add_contact(data: EmergencyContactIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.is_primary:
        db.query(EmergencyContact).filter(EmergencyContact.elder_user_id == user.id).update({"is_primary": False})
    contact = EmergencyContact(elder_user_id=user.id, name=data.name,
                               relationship_type=data.relationship_type, phone=data.phone,
                               is_primary=data.is_primary)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return {"id": contact.id, "name": contact.name, "phone": contact.phone}


@router.get("/logs/{event_id}")
def event_logs(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.get(EmergencyEvent, event_id)
    if event is None or event.elder_user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")
    rows = db.query(EmergencyLog).filter(EmergencyLog.event_id == event_id).order_by(EmergencyLog.id.asc()).all()
    return [
        {"log_type": r.log_type, "detail": r.detail, "created_at": r.created_at.isoformat()}
        for r in rows
    ]
