"""Values for the seeded demo data.

The demo card token is derived from the patient's address rather than drawn at
random. That matters on a host with an ephemeral filesystem and no volume: the
database is rebuilt from the seed on every boot, and a random token would mean
the code printed on a patient's card stopped working every time the service
restarted. A derived token gives the same card every time.

This applies to seeded demo data only. A token a patient issues from the card
screen with "Regenerate card" is still random, and the seeded accounts are
published demo credentials, so a predictable token gives nothing away that
logging in with `aarav@abha.dev` does not already give.
"""

import hashlib

_PREFIX = "abha-demo-card"


def demo_card_token(email: str) -> str:
    """The emergency card token for a seeded demo patient."""
    return hashlib.sha256(f"{_PREFIX}:{email}".encode()).hexdigest()[:32]
