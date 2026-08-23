from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, UserProfile
from app.api.deps import get_current_user
from app.schemas.auth import UserOut

router = APIRouter(prefix="/users", tags=["users"])


class ProfileUpdate(BaseModel):
    gender: str | None = None
    city: str | None = None
    avatar_url: str | None = None
    is_accessible_mode: bool | None = None
    emergency_notes: str | None = None


def _user_out(user: User) -> UserOut:
    p = user.profile
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        role=user.role.code if user.role else "",
        date_of_birth=p.date_of_birth.isoformat() if p and p.date_of_birth else None,
        gender=p.gender if p else None,
        city=p.city if p else None,
        avatar_url=p.avatar_url if p else None,
        is_accessible_mode=p.is_accessible_mode if p else False,
    )


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return _user_out(user)


@router.patch("/me", response_model=UserOut)
def update_me(data: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(user)
    return _user_out(user)
