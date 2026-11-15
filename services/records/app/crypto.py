import hashlib
import hmac
import json
import os

from Crypto.Cipher import AES

KEY = os.getenv("TRAUMA_KEY", "abha-demo-key-16b").encode()[:16]


def seal(payload: dict) -> tuple[str, str, str]:
    """AES-128-GCM encrypt + HMAC-SHA256 sign a JSON payload.

    Returns (data_hex, nonce_hex, sig_hex). data_hex = ciphertext(16) || tag(16).
    """
    nonce = os.urandom(12)
    cipher = AES.new(KEY, AES.MODE_GCM, nonce=nonce)
    ct, tag = cipher.encrypt_and_digest(json.dumps(payload).encode())
    data = ct + tag
    sig = hmac.new(KEY, data, hashlib.sha256).hexdigest()
    return data.hex(), nonce.hex(), sig


def unseal(data_hex: str, nonce_hex: str, sig: str) -> dict | None:
    """Verify HMAC first, then decrypt. Returns None on tamper or auth failure."""
    data = bytes.fromhex(data_hex)
    expected = hmac.new(KEY, data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    ct, tag = data[:-16], data[-16:]
    cipher = AES.new(KEY, AES.MODE_GCM, nonce=bytes.fromhex(nonce_hex))
    try:
        pt = cipher.decrypt_and_verify(ct, tag)
    except ValueError:
        return None
    return json.loads(pt)
