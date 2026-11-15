from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from services.shared.db import Base


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(index=True)
    patient_id: Mapped[int] = mapped_column(index=True)
    patient_abha_id: Mapped[str] = mapped_column(String(14), default="")
    line_items: Mapped[str] = mapped_column(Text, default="[]")  # JSON [{description, amount}]
    total: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("bills.id"), index=True)
    fhir_claim_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(20), default="SUBMITTED", index=True)  # SUBMITTED|ADJUDICATED|APPROVED|REJECTED
    insurer_note: Mapped[str] = mapped_column(String(400), default="")
    approved_amount: Mapped[float] = mapped_column(Float, default=0.0)
    out_of_pocket: Mapped[float] = mapped_column(Float, default=0.0)
    adjudicated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
