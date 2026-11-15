from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from services.shared import security

bearer = HTTPBearer(auto_error=False)


@dataclass
class UserClaim:
    id: int
    role: str
    abha_id: str | None = None
    name: str = ""


def get_db():
    from records_app.main import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> UserClaim:
    """The records service has no users table; JWTs carry identity as claims."""
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    payload = security.decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return UserClaim(id=int(payload["sub"]), role=payload["role"], abha_id=payload.get("abha_id"))
