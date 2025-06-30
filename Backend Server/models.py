from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class DeviceControl(BaseModel):
    device_id: str
    relay: str
    action: str  # "ON" or "OFF"

class OTAUpdateCheck(BaseModel):
    device_id: str
    current_version: str

class OTARegistration(BaseModel):
    device_id: str
    device_type: str
    current_version: str

class OTAUpdateResponse(BaseModel):
    update_available: bool
    new_version: str
    download_url: str

class OTARegistrationResponse(BaseModel):
    registration_status: bool
    device_token: str

class TimerCreate(BaseModel):
    device_id: str
    relay: str
    action: str
    execute_at: datetime

class TimerResponse(BaseModel):
    msg: str
    timer_id: str = None

class TimerInfo(BaseModel):
    timer_id: str
    relay: str
    action: str
    execute_at: datetime

class TimersListResponse(BaseModel):
    timers: List[TimerInfo]

class TimerDeleteResponse(BaseModel):
    msg: str

class DeviceRegister(BaseModel):
    device_id: str
    device_name: str
    room_name: str  # Name of the room to add the device to

class DeviceSchedule(BaseModel):
    action: str  # "ON" or "OFF"
    time: str    # "HH:MM" 24-hour format
    days_of_week: List[str]  # e.g., ["Monday", "Wednesday"]
    schedule_id: Optional[str] = None  # For updates