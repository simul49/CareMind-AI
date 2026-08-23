from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import AiInsight, User
from app.api.deps import get_current_user
from app.services import ai_service
from app.schemas.common import ChatIn, ChatOut, ConversationOut, InsightOut

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatOut)
def chat(data: ChatIn, user: User = Depends(get_current_user)):
    conv_id, reply, sources = ai_service.chat_with_user(user, data.conversation_id, data.message)
    return ChatOut(conversation_id=conv_id, reply=reply, sources=sources)


@router.get("/conversations", response_model=list[ConversationOut])
def conversations(user: User = Depends(get_current_user)):
    return ai_service.list_conversations(user.id)


@router.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: int, user: User = Depends(get_current_user)):
    rows = ai_service.list_messages(conversation_id, user.id)
    if rows is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return rows


@router.get("/insights", response_model=list[InsightOut])
def insights(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(AiInsight)
        .filter(AiInsight.user_id == user.id)
        .order_by(AiInsight.created_at.desc())
        .limit(20)
        .all()
    )
    return rows


@router.post("/insights/{insight_id}/read")
def mark_insight_read(insight_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    insight = db.get(AiInsight, insight_id)
    if insight is None or insight.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Insight not found")
    insight.is_read = True
    db.commit()
    return {"status": "ok"}
