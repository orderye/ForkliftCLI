from pydantic import BaseModel


class UserForkliftCreate(BaseModel):
    forklift_model_id: int | None = None
    customer_name: str = ""
    serial_number: str = ""
    product_number: str = ""
    purchase_date: str = ""
    engine_model: str = ""
    notes: str = ""


class UserForkliftOut(BaseModel):
    id: int
    user_id: int
    forklift_model_id: int | None = None
    customer_name: str
    serial_number: str
    engine_model: str
    current_hours: float
    model_name: str = ""
    brand_name: str = ""

    class Config:
        from_attributes = True


class MaintenanceRecordCreate(BaseModel):
    date: str
    fault_description: str = ""
    cause: str = ""
    parts_replaced_json: list = []
    technician: str = ""
    photos_json: list = []
    cost: float = 0
    hours_at_repair: float | None = None
    notes: str = ""


class MaintenanceRecordOut(BaseModel):
    id: int
    forklift_id: int
    date: str
    fault_description: str
    cause: str
    parts_replaced_json: list
    technician: str
    photos_json: list
    cost: float
    hours_at_repair: float | None = None
    notes: str

    class Config:
        from_attributes = True


class ReminderCreate(BaseModel):
    item_type: str
    item_name: str = ""
    interval_type: str = "hours"
    interval_value: float


class ReminderOut(BaseModel):
    id: int
    forklift_id: int
    item_type: str
    item_name: str
    interval_type: str
    interval_value: float
    last_date: str
    next_date: str
    is_active: int

    class Config:
        from_attributes = True
