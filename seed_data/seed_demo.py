"""Insert synthetic provider directory and fixed slots for local demos."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import select
from app.db.session import Base, SessionLocal, engine
from app.models import Doctor, DoctorLanguage, DoctorSlot, Hospital, Specialty

Base.metadata.create_all(bind=engine)


def main():
    db = SessionLocal()
    try:
        if db.scalar(select(Doctor.id).limit(1)):
            print("Seed skipped: provider data already exists.")
            return

        derm = Specialty(name="Dermatology")
        cardio = Specialty(name="Cardiology")
        gp = Specialty(name="General Practice")
        baner = Hospital(name="CareMatch Demo Clinic — Baner", address="Demo Road, Baner", city="Pune", pincode="411045")
        aundh = Hospital(name="CareMatch Demo Clinic — Aundh", address="Sample Avenue, Aundh", city="Pune", pincode="411007")
        db.add_all([derm, cardio, gp, baner, aundh])
        db.flush()

        doctors = [
            Doctor(full_name="Dr. Ananya Deshmukh", specialty=derm, hospital=baner),
            Doctor(full_name="Dr. Rohan Kulkarni", specialty=cardio, hospital=aundh),
            Doctor(full_name="Dr. Meera Shah", specialty=gp, hospital=baner),
        ]
        db.add_all(doctors)
        db.flush()
        for doctor in doctors:
            db.add_all([
                DoctorLanguage(doctor_id=doctor.id, language_code="en"),
                DoctorLanguage(doctor_id=doctor.id, language_code="hi"),
                DoctorLanguage(doctor_id=doctor.id, language_code="mr"),
            ])
            # Generate slots for the next 7 days at 10:00, 10:30, 14:00, and 14:30 IST.
            for day_offset in range(1, 8):
                india_tz = ZoneInfo("Asia/Kolkata")
                date = (datetime.now(india_tz) + timedelta(days=day_offset)).date()
                for hour, minute in [(10, 0), (10, 30), (14, 0), (14, 30)]:
                    start = datetime(date.year, date.month, date.day, hour, minute, tzinfo=india_tz)
                    db.add(DoctorSlot(
                        doctor_id=doctor.id,
                        hospital_id=doctor.hospital_id,
                        start_at=start,
                        end_at=start + timedelta(minutes=30),
                        status="available",
                    ))
        db.commit()
        print(f"Seeded {len(doctors)} synthetic doctors and fixed appointment slots.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
