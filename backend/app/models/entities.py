from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")


class Specialty(Base):
    __tablename__ = "specialties"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    doctors: Mapped[list["Doctor"]] = relationship(back_populates="specialty")


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    doctors: Mapped[list["Doctor"]] = relationship(back_populates="hospital")
    slots: Mapped[list["DoctorSlot"]] = relationship(back_populates="hospital")


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    specialty_id: Mapped[str] = mapped_column(ForeignKey("specialties.id"), index=True, nullable=False)
    hospital_id: Mapped[str] = mapped_column(ForeignKey("hospitals.id"), index=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    accepting_new_patients: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    consultation_type: Mapped[str] = mapped_column(String(24), default="in_person", nullable=False)

    specialty: Mapped[Specialty] = relationship(back_populates="doctors")
    hospital: Mapped[Hospital] = relationship(back_populates="doctors")
    languages: Mapped[list["DoctorLanguage"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")
    slots: Mapped[list["DoctorSlot"]] = relationship(back_populates="doctor")


class DoctorLanguage(Base):
    __tablename__ = "doctor_languages"
    __table_args__ = (UniqueConstraint("doctor_id", "language_code", name="uq_doctor_language"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), index=True, nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)

    doctor: Mapped[Doctor] = relationship(back_populates="languages")


class DoctorSlot(Base):
    __tablename__ = "doctor_slots"
    __table_args__ = (
        UniqueConstraint("doctor_id", "start_at", name="uq_doctor_slot_start"),
        Index("ix_slots_search", "hospital_id", "start_at", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"), index=True, nullable=False)
    hospital_id: Mapped[str] = mapped_column(ForeignKey("hospitals.id"), index=True, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="available", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    doctor: Mapped[Doctor] = relationship(back_populates="slots")
    hospital: Mapped[Hospital] = relationship(back_populates="slots")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="slot")


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("patient_id", "idempotency_key", name="uq_patient_idempotency_key"),
        Index(
            "uq_active_appointment_slot",
            "slot_id",
            unique=True,
            sqlite_where=text("status = 'confirmed'"),
            postgresql_where=text("status = 'confirmed'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True, nullable=False)
    slot_id: Mapped[str] = mapped_column(ForeignKey("doctor_slots.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="confirmed", index=True, nullable=False)
    booking_reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    patient: Mapped[Patient] = relationship(back_populates="appointments")
    slot: Mapped[DoctorSlot] = relationship(back_populates="appointments")
