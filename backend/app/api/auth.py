from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_patient
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Patient
from app.schemas.auth import PatientLogin, PatientOut, PatientRegister, TokenOut

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def register(payload: PatientRegister, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    existing = db.scalar(select(Patient).where(Patient.email == email))
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    patient = Patient(
        full_name=payload.full_name.strip(),
        email=email,
        phone=payload.phone,
        preferred_language=payload.preferred_language,
        password_hash=hash_password(payload.password),
    )
    db.add(patient)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to create account with these details")
    db.refresh(patient)
    return patient


@router.post("/login", response_model=TokenOut)
def login(payload: PatientLogin, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    patient = db.scalar(select(Patient).where(Patient.email == email))
    if patient is None or not patient.is_active or not verify_password(payload.password, patient.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenOut(access_token=create_access_token(patient.id), patient=patient)


@router.get("/me", response_model=PatientOut)
def me(patient: Patient = Depends(get_current_patient)):
    return patient
