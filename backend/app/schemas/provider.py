from datetime import datetime
from pydantic import BaseModel


class ProviderSearch(BaseModel):
    specialty: str | None = None
    city: str | None = None
    preferred_area: str | None = None
    language: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class SlotOut(BaseModel):
    id: str
    start_at: datetime
    end_at: datetime
    status: str


class ProviderOut(BaseModel):
    doctor_id: str
    doctor_name: str
    specialty: str
    hospital_id: str
    hospital_name: str
    address: str
    city: str
    languages: list[str]
    available_slots: list[SlotOut]
    match_reasons: list[str]
