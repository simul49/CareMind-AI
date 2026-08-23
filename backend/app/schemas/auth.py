from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8, max_length=64)
    role: str = Field(default="elder")  # elder / family / doctor / caregiver
    relationship_type: str = "self"
    date_of_birth: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str | None = None
    phone: str | None = None
    role: str = ""
    date_of_birth: str | None = None
    gender: str | None = None
    city: str | None = None
    avatar_url: str | None = None
    is_accessible_mode: bool = False


class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginResponse(AuthOut):
    pass
