from secrets import token_urlsafe

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_patient
from app.db.session import get_db
from app.models import Appointment, DoctorSlot, Patient
from app.schemas.appointment import AppointmentCancel, AppointmentCreate, AppointmentOut

router = APIRouter(prefix="/appointments", tags=["appointments"])


def to_output(appointment: Appointment) -> AppointmentOut:
    return AppointmentOut(
        id=appointment.id,
        booking_reference=appointment.booking_reference,
        status=appointment.status,
        slot_id=appointment.slot_id,
        doctor_name=appointment.slot.doctor.full_name,
        hospital_name=appointment.slot.hospital.name,
        start_at=appointment.slot.start_at,
        end_at=appointment.slot.end_at,
    )


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    if not payload.confirmation:
        raise HTTPException(status_code=400, detail="Explicit confirmation is required")
    if idempotency_key:
        previous = db.scalar(select(Appointment).options(
            joinedload(Appointment.slot).joinedload(DoctorSlot.doctor),
            joinedload(Appointment.slot).joinedload(DoctorSlot.hospital),
        ).where(Appointment.patient_id == patient.id, Appointment.idempotency_key == idempotency_key))
        if previous:
            return to_output(previous)

    slot_stmt = select(DoctorSlot).options(
        joinedload(DoctorSlot.doctor), joinedload(DoctorSlot.hospital)
    ).where(DoctorSlot.id == payload.slot_id, DoctorSlot.status == "available")
    if db.bind and db.bind.dialect.name != "sqlite":
        slot_stmt = slot_stmt.with_for_update()
    slot = db.scalar(slot_stmt)
    if slot is None:
        raise HTTPException(status_code=409, detail="This slot is no longer available. Please search again.")
    if not slot.doctor.active or not slot.doctor.accepting_new_patients or not slot.hospital.active:
        raise HTTPException(status_code=409, detail="This provider is not currently accepting bookings")

    appointment = Appointment(
        patient_id=patient.id,
        slot_id=slot.id,
        status="confirmed",
        booking_reference=f"CM-{token_urlsafe(5).replace('-', '').replace('_', '')[:8].upper()}",
        idempotency_key=idempotency_key,
    )
    slot.status = "booked"
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if idempotency_key:
            previous = db.scalar(select(Appointment).options(
                joinedload(Appointment.slot).joinedload(DoctorSlot.doctor),
                joinedload(Appointment.slot).joinedload(DoctorSlot.hospital),
            ).where(Appointment.patient_id == patient.id, Appointment.idempotency_key == idempotency_key))
            if previous:
                return to_output(previous)
        raise HTTPException(status_code=409, detail="This slot was booked by another request. Please search again.")
    db.refresh(appointment)
    appointment = db.scalar(select(Appointment).options(
        joinedload(Appointment.slot).joinedload(DoctorSlot.doctor),
        joinedload(Appointment.slot).joinedload(DoctorSlot.hospital),
    ).where(Appointment.id == appointment.id))
    return to_output(appointment)


@router.get("", response_model=list[AppointmentOut])
def list_my_appointments(patient: Patient = Depends(get_current_patient), db: Session = Depends(get_db)):
    appointments = db.scalars(select(Appointment).options(
        joinedload(Appointment.slot).joinedload(DoctorSlot.doctor),
        joinedload(Appointment.slot).joinedload(DoctorSlot.hospital),
    ).where(Appointment.patient_id == patient.id).order_by(Appointment.created_at.desc())).unique().all()
    return [to_output(item) for item in appointments]


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(
    appointment_id: str,
    payload: AppointmentCancel,
    patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    if not payload.confirmation:
        raise HTTPException(status_code=400, detail="Explicit confirmation is required")
    appointment = db.scalar(select(Appointment).options(
        joinedload(Appointment.slot).joinedload(DoctorSlot.doctor),
        joinedload(Appointment.slot).joinedload(DoctorSlot.hospital),
    ).where(Appointment.id == appointment_id, Appointment.patient_id == patient.id))
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.status != "confirmed":
        raise HTTPException(status_code=409, detail="Only confirmed appointments can be cancelled")
    appointment.status = "cancelled"
    appointment.slot.status = "available"
    db.commit()
    db.refresh(appointment)
    return to_output(appointment)
