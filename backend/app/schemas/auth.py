from datetime import datetime
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11)
    password: str = Field(..., min_length=6)
    nickname: str = ""


class UserLogin(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: int
    phone: str | None = None
    email: str | None = None
    nickname: str
    avatar: str
    subscription_level: str = "free"
    subscription_expires_at: datetime | None = None
    is_active: bool = True
    device_token: str = ""

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    nickname: str | None = None
    avatar: str | None = None
    email: str | None = None
