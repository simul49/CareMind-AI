"""Notifications feed — a merged, role-aware inbox.

Sources (ephemeral, built on the fly — cheap for a hackathon demo):
- AI insights (elder)
- Today's pending medicine doses (elder)
- Active emergencies in my care circle (family / caregiver / doctor)
- Recently analyzed reports (elder)
- Recent chat messages from others

`id` carries a type prefix so the frontend can mark a source read
(only insights are persisted via /ai/insights/{id}/read).
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import (
    AiInsight,
    CareCircle,
    CareCircleMember,
    Conversation,
    ConversationMember,
    EmergencyEvent,
    HealthReport,
    MedicationLog,
    Medicine,
    Message,
    User,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items: list[dict] = []
    now = datetime.utcnow()
    today = now.date()
    tomorrow = today + timedelta(days=1)

    # --- AI insights (elder) ---
    insights = (
        db.query(AiInsight)
        .filter(AiInsight.user_id == user.id)
        .order_by(AiInsight.created_at.desc())
        .limit(5)
        .all()
    )
    for i in insights:
        icon = "🚨" if i.severity == "critical" else ("🔎" if i.severity == "warning" else "💡")
        items.append({
            "id": f"insight-{i.id}",
            "type": "insight",
            "icon": icon,
            "title": i.title or "CareMind insight",
            "content": i.content,
            "time": i.created_at.isoformat(),
            "is_read": bool(i.is_read),
            "link": "/app/health",
            "severity": i.severity,
        })

    # --- Today's pending doses (elder) ---
    doses = (
        db.query(MedicationLog)
        .join(Medicine, MedicationLog.medicine_id == Medicine.id)
        .filter(
            MedicationLog.user_id == user.id,
            MedicationLog.scheduled_for >= datetime.combine(today, datetime.min.time()),
            MedicationLog.scheduled_for < datetime.combine(tomorrow, datetime.min.time()),
            MedicationLog.status == "pending",
        )
        .order_by(MedicationLog.scheduled_for.asc())
        .limit(4)
        .all()
    )
    for d in doses:
        items.append({
            "id": f"dose-{d.id}",
            "type": "medicine",
            "icon": "💊",
            "title": f"Medicine due · {d.medicine.name if d.medicine else 'Medication'}",
            "content": f"Scheduled for {d.scheduled_for.strftime('%I:%M %p')} — tap to confirm taking it.",
            "time": d.scheduled_for.isoformat(),
            "is_read": True,
            "link": "/app/medicines",
            "severity": "info",
        })

    # --- Active emergencies in my care circle (family / caregiver / doctor) ---
    circle = (
        db.query(CareCircle)
        .join(CareCircleMember, CareCircleMember.care_circle_id == CareCircle.id)
        .filter(CareCircleMember.user_id == user.id)
        .first()
    )
    if circle is not None:
        member_ids = [
            m.user_id
            for m in db.query(CareCircleMember).filter(CareCircleMember.care_circle_id == circle.id).all()
        ]
        events = (
            db.query(EmergencyEvent)
            .filter(
                EmergencyEvent.elder_user_id.in_(member_ids),
                EmergencyEvent.status == "active",
            )
            .order_by(EmergencyEvent.created_at.desc())
            .limit(3)
            .all()
        )
        for e in events:
            elder = db.get(User, e.elder_user_id)
            trigger = "SOS button" if e.trigger_type == "manual" else e.trigger_type.replace("_", " ").title()
            items.append({
                "id": f"emergency-{e.id}",
                "type": "emergency",
                "icon": "🚨",
                "title": f"Emergency · {elder.full_name if elder else 'Care circle member'}",
                "content": f"{trigger} pressed at {e.created_at.strftime('%I:%M %p')} — take action now.",
                "time": e.created_at.isoformat(),
                "is_read": True,
                "link": "/app/emergency",
                "severity": "critical",
            })

    # --- Recent analyzed reports (elder) ---
    reports = (
        db.query(HealthReport)
        .filter(HealthReport.user_id == user.id, HealthReport.status == "analyzed")
        .order_by(HealthReport.analyzed_at.desc())
        .limit(3)
        .all()
    )
    for r in reports:
        snippet = (r.summary or "Your report analysis is ready.")[:120]
        items.append({
            "id": f"report-{r.id}",
            "type": "report",
            "icon": "📄",
            "title": f"Report analyzed · {r.title}",
            "content": snippet + ("…" if len(r.summary or "") > 120 else ""),
            "time": (r.analyzed_at or r.created_at).isoformat(),
            "is_read": True,
            "link": "/app/reports",
            "severity": "info",
        })

    # --- Recent chat messages from others ---
    convs = (
        db.query(Conversation)
        .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
        .filter(ConversationMember.user_id == user.id)
        .all()
    )
    for c in convs:
        last = (
            db.query(Message)
            .filter(Message.conversation_id == c.id, Message.sender_id != user.id)
            .order_by(Message.id.desc())
            .first()
        )
        if last and last.created_at >= now - timedelta(days=2):
            sender = db.get(User, last.sender_id)
            items.append({
                "id": f"msg-{last.id}",
                "type": "chat",
                "icon": "💬",
                "title": f"Message from {sender.full_name if sender else 'family'}",
                "content": last.content[:120],
                "time": last.created_at.isoformat(),
                "is_read": True,
                "link": "/app/chat",
                "severity": "info",
            })

    items.sort(key=lambda x: x["time"], reverse=True)
    return {"count": len(items), "items": items[:30]}
