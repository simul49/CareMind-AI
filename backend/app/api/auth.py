from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.models import Role, User, UserProfile
from app.api.deps import get_current_user
from app.schemas.auth import AuthOut, LoginIn, RegisterIn, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(user: User) -> UserOut:
    profile = user.profile
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        role=user.role.code if user.role else "",
        date_of_birth=profile.date_of_birth.isoformat() if profile and profile.date_of_birth else None,
        gender=profile.gender if profile else None,
        city=profile.city if profile else None,
        avatar_url=profile.avatar_url if profile else None,
        is_accessible_mode=profile.is_accessible_mode if profile else False,
    )


def _build_auth(user: User) -> AuthOut:
    return AuthOut(
        access_token=create_access_token(str(user.id), user.role.code if user.role else ""),
        user=_user_out(user),
    )


@router.post("/register", response_model=AuthOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == str(data.email).lower()).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    role = db.query(Role).filter(Role.code == data.role).first()
    if role is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown role")
    user = User(
        full_name=data.full_name.strip(),
        email=str(data.email).lower(),
        phone=data.phone,
        password_hash=hash_password(data.password),
        role_id=role.id,
        is_verified=True,
    )
    db.add(user)
    db.flush()
    dob = None
    if data.date_of_birth:
        try:
            dob = datetime.strptime(data.date_of_birth, "%Y-%m-%d").date()
        except ValueError:
            dob = None
    db.add(
        UserProfile(
            user_id=user.id,
            date_of_birth=dob,
            primary_language="english",
        )
    )
    db.commit()
    db.refresh(user)
    return _build_auth(user)


@router.post("/login", response_model=AuthOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(data.email).lower()).first()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    return _build_auth(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _user_out(user)
