from records_app.crypto import seal, unseal


def test_round_trip():
    payload = {"blood_group": "O+", "allergies": ["Penicillin"]}
    data_hex, nonce_hex, sig = seal(payload)
    assert unseal(data_hex, nonce_hex, sig) == payload


def test_tampered_signature_rejected():
    payload = {"a": 1}
    data_hex, nonce_hex, sig = seal(payload)
    bad_sig = ("0" * 64) if sig[0] != "0" else ("1" * 64)
    assert unseal(data_hex, nonce_hex, bad_sig) is None


def test_tampered_ciphertext_rejected():
    payload = {"a": 1}
    data_hex, nonce_hex, sig = seal(payload)
    raw = bytearray(bytes.fromhex(data_hex))
    raw[0] ^= 0xFF
    assert unseal(bytes(raw).hex(), nonce_hex, sig) is None


def test_sig_is_hmac_of_ciphertext():
    import hashlib, hmac
    from records_app.crypto import KEY

    payload = {"b": 2}
    data_hex, nonce_hex, sig = seal(payload)
    expected = hmac.new(KEY, bytes.fromhex(data_hex), hashlib.sha256).hexdigest()
    assert sig == expected
