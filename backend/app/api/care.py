"""Care Circle — Moments feed (posts) + family chat."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import (
    CareCircle,
    CareCircleMember,
    Conversation,
    ConversationMember,
    Message,
    Post,
    PostReaction,
    User,
)
from app.api.deps import get_current_user
from app.schemas.common import FamilyMessageIn, FamilyMessageOut, PostIn, PostOut

router = APIRouter(prefix="/care", tags=["care"])


def _user_circle(db: Session, user: User) -> CareCircle | None:
    return (
        db.query(CareCircle)
        .join(CareCircleMember)
        .filter(CareCircleMember.user_id == user.id)
        .order_by(CareCircle.id.asc())
        .first()
    )


@router.get("/circle")
def my_circle(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    circle = _user_circle(db, user)
    if circle is None:
        return {"id": None, "name": None, "members": []}
    members = db.query(CareCircleMember).filter(CareCircleMember.care_circle_id == circle.id).all()
    out = []
    for m in members:
        u = db.get(User, m.user_id)
        out.append({"user_id": m.user_id, "name": u.full_name if u else "?",
                    "relationship_type": m.relationship_type,
                    "role": u.role.code if u and u.role else ""})
    return {"id": circle.id, "name": circle.name, "members": out}


# ---------------------------------------------------------------- Moments
@router.get("/posts", response_model=list[PostOut])
def posts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    circle = _user_circle(db, user)
    circle_ids = [circle.id] if circle else []
    rows = (
        db.query(Post)
        .filter(Post.care_circle_id.in_(circle_ids) if circle_ids else Post.visibility == "public")
        .order_by(Post.created_at.desc())
        .limit(30)
        .all()
    )
    out = []
    for p in rows:
        reactions = db.query(PostReaction).filter(PostReaction.post_id == p.id).count()
        mine = (
            db.query(PostReaction)
            .filter(PostReaction.post_id == p.id, PostReaction.user_id == user.id)
            .first()
        )
        author = db.get(User, p.author_id)
        out.append(PostOut(
            id=p.id, author_id=p.author_id,
            author_name=author.full_name if author else "?",
            content=p.content, image_url=p.image_url,
            created_at=p.created_at, reaction_count=reactions,
            my_reaction=mine.reaction_type if mine else None,
        ))
    return out


@router.post("/posts", response_model=PostOut)
def create_post(data: PostIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    circle = _user_circle(db, user)
    post = Post(author_id=user.id, content=data.content, visibility=data.visibility,
                care_circle_id=circle.id if circle else None)
    db.add(post)
    db.commit()
    db.refresh(post)
    return PostOut(id=post.id, author_id=post.author_id, author_name=user.full_name,
                   content=post.content, image_url=None, created_at=post.created_at,
                   reaction_count=0, my_reaction=None)


@router.post("/posts/{post_id}/react")
def react(post_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    existing = (
        db.query(PostReaction)
        .filter(PostReaction.post_id == post_id, PostReaction.user_id == user.id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return {"post_id": post_id, "reacted": False}
    db.add(PostReaction(post_id=post_id, user_id=user.id, reaction_type="like"))
    db.commit()
    return {"post_id": post_id, "reacted": True}


# ---------------------------------------------------------------- family chat
@router.get("/conversations")
def conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Conversation)
        .join(ConversationMember)
        .filter(ConversationMember.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    out = []
    for c in rows:
        last = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.id.desc()).first()
        member_names = []
        for m in c.members:
            u = db.get(User, m.user_id)
            if u and u.id != user.id:
                member_names.append(u.full_name)
        out.append({
            "id": c.id,
            "conversation_type": c.conversation_type,
            "title": c.title or ", ".join(member_names) or "Family",
            "last_message": last.content if last else "",
            "last_at": last.created_at.isoformat() if last else None,
        })
    return out


@router.get("/conversations/{conversation_id}/messages", response_model=list[FamilyMessageOut])
def conversation_messages(conversation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.get(Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    is_member = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id, ConversationMember.user_id == user.id
    ).first()
    if is_member is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member")
    rows = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.id.asc()).all()
    out = []
    for m in rows:
        sender = db.get(User, m.sender_id)
        out.append(FamilyMessageOut(
            id=m.id, conversation_id=m.conversation_id, sender_id=m.sender_id,
            sender_name=sender.full_name if sender else "?",
            content=m.content, created_at=m.created_at,
        ))
    return out


@router.post("/conversations/{conversation_id}/messages", response_model=FamilyMessageOut)
def send_message(conversation_id: int, data: FamilyMessageIn, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    conv = db.get(Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    is_member = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id, ConversationMember.user_id == user.id
    ).first()
    if is_member is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member")
    msg = Message(conversation_id=conversation_id, sender_id=user.id, content=data.content)
    db.add(msg)
    conv.updated_at = msg.created_at
    db.commit()
    db.refresh(msg)
    return FamilyMessageOut(id=msg.id, conversation_id=msg.conversation_id, sender_id=user.id,
                            sender_name=user.full_name, content=msg.content, created_at=msg.created_at)
