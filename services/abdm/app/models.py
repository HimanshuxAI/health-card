from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from services.shared.db import Base


class CareContext(Base):
    __tablename__ = "care_contexts"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(index=True)
    record_ref: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="LINKED")  # LINKED|CONSENT_PENDING|ACTIVE
    linked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AbdmLog(Base):
    __tablename__ = "abdm_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    direction: Mapped[str] = mapped_column(String(4))  # IN | OUT
    endpoint: Mapped[str] = mapped_column(String(200))
    payload_snippet: Mapped[str] = mapped_column(Text, default="")
    status_code: Mapped[int] = mapped_column(default=200)
    latency_ms: Mapped[int] = mapped_column(default=0)
