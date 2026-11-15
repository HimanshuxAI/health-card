from deck.content import SLIDES


def test_slide_notes_have_approved_word_count() -> None:
    word_counts = {slide.index: len(slide.notes.split()) for slide in SLIDES}

    assert all(35 <= count <= 60 for count in word_counts.values()), word_counts
