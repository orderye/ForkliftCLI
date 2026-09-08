from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.core.security import get_current_user
from app.models.user import User
from app.models.maintenance import UserForklift, MaintenanceRecord, MaintenanceReminder
from app.schemas.maintenance import (
    UserForkliftCreate, UserForkliftOut,
    MaintenanceRecordCreate, MaintenanceRecordOut,
    ReminderCreate, ReminderOut,
)

router = APIRouter(prefix="/my-forklifts", tags=["我的叉车"])


@router.get("", response_model=list[UserForkliftOut])
@safe_api
def list_my_forklifts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(UserForklift)
        .filter(UserForklift.user_id == current_user.id)
        .all()
    )
    result = []
    for item in items:
        out = UserForkliftOut.model_validate(item)
        if item.forklift_model_id:
            from app.models.forklift import ForkliftModel
            model = db.query(ForkliftModel).filter(ForkliftModel.id == item.forklift_model_id).first()
            if model:
                out.model_name = model.name
                out.brand_name = model.series.brand.name if model.series else ""
        result.append(out)
    return result


@router.post("", response_model=UserForkliftOut)
@safe_api
def add_forklift(
    data: UserForkliftCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    forklift = UserForklift(
        user_id=current_user.id,
        forklift_model_id=data.forklift_model_id,
        customer_name=data.customer_name,
        serial_number=data.serial_number,
        product_number=data.product_number,
        purchase_date=data.purchase_date,
        engine_model=data.engine_model,
        notes=data.notes,
    )
    db.add(forklift)
    db.commit()
    db.refresh(forklift)
    return UserForkliftOut.model_validate(forklift)


@router.get("/{forklift_id}", response_model=UserForkliftOut)
@safe_api
def get_forklift(
    forklift_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(UserForklift)
        .filter(UserForklift.id == forklift_id, UserForklift.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="叉车档案不存在")
    return UserForkliftOut.model_validate(item)


@router.put("/{forklift_id}", response_model=UserForkliftOut)
@safe_api
def update_forklift(
    forklift_id: int,
    data: UserForkliftCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(UserForklift)
        .filter(UserForklift.id == forklift_id, UserForklift.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="叉车档案不存在")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return UserForkliftOut.model_validate(item)


@router.delete("/{forklift_id}")
@safe_api
def delete_forklift(
    forklift_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(UserForklift)
        .filter(UserForklift.id == forklift_id, UserForklift.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="叉车档案不存在")
    db.delete(item)
    db.commit()
    return {"detail": "已删除"}


# ========== 维修记录 ==========

@router.get("/{forklift_id}/records", response_model=list[MaintenanceRecordOut])
@safe_api
def list_records(
    forklift_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.forklift_id == forklift_id)
        .order_by(MaintenanceRecord.date.desc())
        .all()
    )


@router.post("/{forklift_id}/records", response_model=MaintenanceRecordOut)
@safe_api
def add_record(
    forklift_id: int,
    data: MaintenanceRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = MaintenanceRecord(forklift_id=forklift_id, **data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return MaintenanceRecordOut.model_validate(record)


# ========== 保养提醒 ==========

@router.get("/{forklift_id}/reminders", response_model=list[ReminderOut])
@safe_api
def list_reminders(
    forklift_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(MaintenanceReminder)
        .filter(MaintenanceReminder.forklift_id == forklift_id)
        .all()
    )


@router.post("/{forklift_id}/reminders", response_model=ReminderOut)
@safe_api
def add_reminder(
    forklift_id: int,
    data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reminder = MaintenanceReminder(forklift_id=forklift_id, **data.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return ReminderOut.model_validate(reminder)


@router.put("/reminders/{reminder_id}", response_model=ReminderOut)
@safe_api
def update_reminder(
    reminder_id: int,
    data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reminder = db.query(MaintenanceReminder).filter(
        MaintenanceReminder.id == reminder_id
    ).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")

    forklift = db.query(UserForklift).filter(
        UserForklift.id == reminder.forklift_id,
        UserForklift.user_id == current_user.id,
    ).first()
    if not forklift:
        raise HTTPException(status_code=403, detail="无权操作")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(reminder, field, value)
    db.commit()
    db.refresh(reminder)
    return ReminderOut.model_validate(reminder)


@router.patch("/reminders/{reminder_id}/toggle", response_model=ReminderOut)
@safe_api
def toggle_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """切换提醒启用状态"""
    reminder = db.query(MaintenanceReminder).filter(
        MaintenanceReminder.id == reminder_id
    ).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")

    forklift = db.query(UserForklift).filter(
        UserForklift.id == reminder.forklift_id,
        UserForklift.user_id == current_user.id,
    ).first()
    if not forklift:
        raise HTTPException(status_code=403, detail="无权操作")

    reminder.is_active = 0 if reminder.is_active == 1 else 1
    db.commit()
    db.refresh(reminder)
    return ReminderOut.model_validate(reminder)


@router.delete("/reminders/{reminder_id}")
@safe_api
def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reminder = db.query(MaintenanceReminder).filter(
        MaintenanceReminder.id == reminder_id
    ).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")

    forklift = db.query(UserForklift).filter(
        UserForklift.id == reminder.forklift_id,
        UserForklift.user_id == current_user.id,
    ).first()
    if not forklift:
        raise HTTPException(status_code=403, detail="无权操作")

    db.delete(reminder)
    db.commit()
    return {"detail": "已删除"}
