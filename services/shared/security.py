from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from services.shared.config import JWT_SECRET, JWT_ALG, JWT_EXP_HOURS


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(sub: str, role: str, abha_id: str | None = None) -> str:
    payload = {
        "sub": sub,
        "role": role,
        "abha_id": abha_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXP_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        return None
