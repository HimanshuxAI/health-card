import re

from deck.content import SLIDES


EXPECTED_TITLES = (
    "At 03:12, the ambulance doesn’t need a login.",
    "Critical context arrives fragmented.",
    "One scan. The right context. Immediately.",
    "One patient. Three workspaces.",
    "Anatomy of a health card.",
    "Sealed by default. Opened by need.",
    "Native data. No translation drama.",
    "Panic → panel → people.",
    "Measured, not marketed.",
    "A health record that arrives before the ambulance does.",
)


def test_slide_content_invariants() -> None:
    indexes = [slide.index for slide in SLIDES]

    assert len(SLIDES) == 10
    assert indexes == list(range(1, 11))
    assert len(set(indexes)) == len(indexes)
    assert all(slide.evidence for slide in SLIDES)
    assert all(all(item.strip() for item in slide.evidence) for slide in SLIDES)

    word_counts = {slide.index: len(slide.notes.split()) for slide in SLIDES}
    assert all(35 <= count <= 60 for count in word_counts.values()), word_counts


def test_slide_copy_uses_repository_factual_claims() -> None:
    assert tuple(slide.title for slide in SLIDES) == EXPECTED_TITLES

    all_copy = " ".join(
        slide.message + " " + " ".join(slide.evidence) + " " + slide.notes
        for slide in SLIDES
    )
    assert re.search(r"\bsigned\b", all_copy, flags=re.IGNORECASE) is None

    assert SLIDES[0].message == (
        "A portable emergency identity that works before a responder login."
    )
    assert "authenticated card" in SLIDES[0].notes
    assert "not yet checked" in SLIDES[1].notes

    assert SLIDES[2].evidence[0] == "Opaque random QR token"
    assert "lookup token" in SLIDES[2].notes
    assert "HMAC-SHA256" in SLIDES[2].notes
    assert "before AES-128-GCM decryption" in SLIDES[2].notes

    assert "16-byte random QR token" in SLIDES[5].evidence
    assert any(
        "HMAC" in item
        and "encrypted stored trauma profile" in item
        and "before decryption" in item
        for item in SLIDES[5].evidence
    )
    assert "before attempting decryption" in SLIDES[5].notes

    assert "One-command service startup" in SLIDES[8].evidence
    assert "gateway and five services plus a seed job for seeded data" in SLIDES[8].notes
    assert "Next.js frontend runs separately" in SLIDES[8].notes

    assert "60-second" not in SLIDES[9].message
    assert "60-second" not in SLIDES[9].notes
