"""Emergency (SOS) service — coordinates the alert flow.

Demo behavior:
  - Creates an EmergencyEvent
  - "Notifies" each emergency contact (logs an entry — simulated)
  - Finds a nearby hospital (simulated)
  - Sends a system message to the family conversation
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import (
    Conversation,
    ConversationMember,
    EmergencyContact,
    EmergencyEvent,
    EmergencyLog,
    Message,
    User,
)

NEARBY_HOSPITALS = [
    {"name": "City General Hospital", "distance_km": 1.8, "eta_minutes": 5, "phone": "+1 (555) 010-1000"},
    {"name": "St. Mary's Care Hospital", "distance_km": 2.4, "eta_minutes": 7, "phone": "+1 (555) 010-2000"},
    {"name": "Lakeside Medical Center", "distance_km": 3.1, "eta_minutes": 9, "phone": "+1 (555) 010-3000"},
]


def trigger_sos(db: Session, elder: User, trigger_type: str, location_label: str | None,
                lat: float | None, lng: float | None) -> dict:
    event = EmergencyEvent(
        elder_user_id=elder.id,
        trigger_type=trigger_type,
        status="active",
        location_label=location_label or "Home — 12 Rosewood Lane, Apt 4B",
        location_lat=lat,
        location_lng=lng,
        started_at=datetime.utcnow(),
    )
    db.add(event)
    db.flush()

    contacts = db.query(EmergencyContact).filter(EmergencyContact.elder_user_id == elder.id).all()
    notified = []
    for c in contacts:
        db.add(EmergencyLog(event_id=event.id, log_type="contact_notified",
                            detail=f"SMS sent to {c.name} ({c.phone})"))
        notified.append({"name": c.name, "phone": c.phone, "relationship": c.relationship_type})

    hospital = NEARBY_HOSPITALS[0]
    db.add(EmergencyLog(event_id=event.id, log_type="hospital_located",
                        detail=f"Nearby hospital: {hospital['name']} ({hospital['distance_km']} km)"))

    # Notify family conversation
    family_conv = (
        db.query(Conversation)
        .join(ConversationMember)
        .filter(ConversationMember.user_id == elder.id, Conversation.conversation_type == "family")
        .first()
    )
    if family_conv:
        db.add(Message(
            conversation_id=family_conv.id,
            sender_id=elder.id,
            content=f"SOS ALERT: {elder.full_name} pressed the emergency button at "
                    f"{datetime.utcnow().strftime('%H:%M')}. Location: {event.location_label}. "
                    f"Nearest hospital: {hospital['name']}. Please call immediately.",
            message_type="system",
        ))

    db.commit()
    return {
        "event_id": event.id,
        "status": "active",
        "location_label": event.location_label,
        "hospital": hospital,
        "contacts_notified": notified,
        "message": "Emergency alert sent. Help is on the way. Stay calm and stay where you are."
    }


def resolve_event(db: Session, event: EmergencyEvent, summary: str | None) -> dict:
    event.status = "resolved"
    event.resolved_at = datetime.utcnow()
    event.summary = summary or "Resolved by user."
    db.add(EmergencyLog(event_id=event.id, log_type="resolved", detail=event.summary))
    db.commit()
    return {"event_id": event.id, "status": "resolved"}
