from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str
    role: Literal["patient", "hospital"]
    abha_id: str | None = None
    phone: str | None = None
    hospital_name: str | None = None


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    abha_id: str | None
    name: str
    user_id: int


class EkycIn(BaseModel):
    abha_id: str


class EkycOut(BaseModel):
    verified: bool
    abha_id: str
    txn_id: str
    name_masked: str
    ts: datetime


class ConsentIn(BaseModel):
    patient_id: int
    hospital_id: int
    scope: str = "records.read"


class ConsentOut(BaseModel):
    id: int
    patient_id: int
    hospital_id: int
    scope: str
    status: str
    granted_at: datetime
