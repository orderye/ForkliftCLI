from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.core.error_handler import safe_api
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserOut, UserUpdate

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse)
@safe_api
def register(data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.phone == data.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="该手机号已注册")

    user = User(
        phone=data.phone,
        password_hash=hash_password(data.password),
        nickname=data.nickname or f"用户{data.phone[-4:]}",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
@safe_api
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == data.phone).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="手机号或密码错误")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.get("/profile", response_model=UserOut)
@safe_api
def get_profile(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.put("/profile", response_model=UserOut)
@safe_api
def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.nickname is not None:
        current_user.nickname = data.nickname
    if data.avatar is not None:
        current_user.avatar = data.avatar
    if data.email is not None:
        current_user.email = data.email
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)
