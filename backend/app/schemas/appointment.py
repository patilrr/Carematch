from datetime import datetime
from pydantic import BaseModel, Field


class AppointmentCreate(BaseModel):
    slot_id: str
    confirmation: bool


class AppointmentReschedule(BaseModel):
    new_slot_id: str
    confirmation: bool


class AppointmentOut(BaseModel):
    id: str
    booking_reference: str
    status: str
    slot_id: str
    doctor_name: str
    hospital_name: str
    start_at: datetime
    end_at: datetime


class AppointmentCancel(BaseModel):
    confirmation: bool
    reason: str | None = Field(default=None, max_length=250)
