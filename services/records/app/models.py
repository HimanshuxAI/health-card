from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from services.shared.db import Base


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), default="")
    blood_group: Mapped[str] = mapped_column(String(5), default="")
    allergies: Mapped[str] = mapped_column(Text, default="[]")       # JSON list
    chronic_conditions: Mapped[str] = mapped_column(Text, default="[]")
    medications: Mapped[str] = mapped_column(Text, default="[]")
    emergency_contacts: Mapped[str] = mapped_column(Text, default="[]")  # JSON [{name, phone, relation}]
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class HealthRecord(Base):
    __tablename__ = "health_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(index=True)   # user_id of patient
    type: Mapped[str] = mapped_column(String(40))          # Prescription | DiagnosticReport | Immunization
    title: Mapped[str] = mapped_column(String(200))
    fhir_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[int] = mapped_column(default=0)     # hospital user id
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TraumaProfile(Base):
    __tablename__ = "trauma_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(unique=True, index=True)
    encrypted_blob: Mapped[str] = mapped_column(Text)      # hex: ciphertext(16) || tag(16)
    nonce: Mapped[str] = mapped_column(String(24))         # hex
    hmac_sha256: Mapped[str] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class QrToken(Base):
    __tablename__ = "qr_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(index=True)
    token: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
