from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Doctor, DoctorSlot, Hospital
from app.schemas.provider import ProviderOut, ProviderSearch, SlotOut

router = APIRouter(prefix="/providers", tags=["providers"])


@router.post("/search", response_model=list[ProviderOut])
def search_providers(payload: ProviderSearch, db: Session = Depends(get_db)):
    stmt = select(Doctor).options(
        selectinload(Doctor.specialty),
        selectinload(Doctor.hospital),
        selectinload(Doctor.languages),
    ).where(Doctor.active.is_(True), Doctor.accepting_new_patients.is_(True), Hospital.active.is_(True))
    stmt = stmt.join(Hospital, Doctor.hospital_id == Hospital.id)
    if payload.specialty:
        stmt = stmt.join(Doctor.specialty).where(Doctor.specialty.has(name=payload.specialty))
    if payload.city:
        stmt = stmt.where(Hospital.city.ilike(payload.city))
    if payload.preferred_area:
        stmt = stmt.where(Hospital.address.ilike(f"%{payload.preferred_area}%"))

    doctors = db.scalars(stmt.order_by(Doctor.full_name)).unique().all()
    results: list[ProviderOut] = []
    for doctor in doctors:
        languages = [item.language_code for item in doctor.languages]
        if payload.language and payload.language.lower() not in [code.lower() for code in languages]:
            continue
        slot_stmt = select(DoctorSlot).where(
            DoctorSlot.doctor_id == doctor.id,
            DoctorSlot.status == "available",
        )
        if payload.date_from:
            slot_stmt = slot_stmt.where(DoctorSlot.start_at >= payload.date_from)
        if payload.date_to:
            slot_stmt = slot_stmt.where(DoctorSlot.start_at < payload.date_to)
        slots = db.scalars(slot_stmt.order_by(DoctorSlot.start_at).limit(10)).all()
        if payload.date_from or payload.date_to:
            if not slots:
                continue
        reasons = [f"Specialty: {doctor.specialty.name}"]
        if payload.city:
            reasons.append(f"Located in {doctor.hospital.city}")
        if payload.preferred_area:
            reasons.append(f"Address matches {payload.preferred_area}")
        if payload.language:
            reasons.append(f"Language supported: {payload.language}")
        results.append(ProviderOut(
            doctor_id=doctor.id,
            doctor_name=doctor.full_name,
            specialty=doctor.specialty.name,
            hospital_id=doctor.hospital.id,
            hospital_name=doctor.hospital.name,
            address=doctor.hospital.address,
            city=doctor.hospital.city,
            languages=languages,
            available_slots=[SlotOut(id=s.id, start_at=s.start_at, end_at=s.end_at, status=s.status) for s in slots],
            match_reasons=reasons,
        ))
    return results


@router.get("/slots", response_model=list[SlotOut])
def list_slots(doctor_id: str, db: Session = Depends(get_db)):
    slots = db.scalars(select(DoctorSlot).where(
        DoctorSlot.doctor_id == doctor_id,
        DoctorSlot.status == "available",
    ).order_by(DoctorSlot.start_at)).all()
    return [SlotOut(id=s.id, start_at=s.start_at, end_at=s.end_at, status=s.status) for s in slots]
