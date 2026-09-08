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
    role: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    nickname: str | None = None
    avatar: str | None = None
    email: str | None = None
