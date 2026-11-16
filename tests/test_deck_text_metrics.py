from deck.text_metrics import measure_wrapped_text_height


def test_wrapped_text_measurement_accounts_for_wrapping() -> None:
    text = "Emergency context should arrive without a responder login."

    narrow_height = measure_wrapped_text_height(
        text,
        width_inches=1.2,
        font_name="Arial",
        font_size_pt=12,
    )
    wide_height = measure_wrapped_text_height(
        text,
        width_inches=4.0,
        font_name="Arial",
        font_size_pt=12,
    )

    assert narrow_height > wide_height


def test_wrapped_text_measurement_handles_explicit_newlines() -> None:
    single_line = measure_wrapped_text_height(
        "One line",
        width_inches=3.0,
        font_name="Georgia",
        font_size_pt=12,
    )
    two_lines = measure_wrapped_text_height(
        "One line\nSecond line",
        width_inches=3.0,
        font_name="Georgia",
        font_size_pt=12,
    )

    assert two_lines > single_line


def test_wrapped_text_measurement_detects_an_insufficient_box() -> None:
    measured_height = measure_wrapped_text_height(
        "This deliberately narrow box forces several wrapped lines of text.",
        width_inches=0.8,
        font_name="Courier New",
        font_size_pt=12,
    )

    assert measured_height > 0.5


def test_overlong_unbreakable_identifier_is_detected_as_horizontal_overflow() -> None:
    identifier = "0123456789abcdef" * 4

    measured_height = measure_wrapped_text_height(
        identifier,
        width_inches=0.8,
        font_name="Courier New",
        font_size_pt=12,
    )
    single_line_height = measure_wrapped_text_height(
        "X",
        width_inches=0.8,
        font_name="Courier New",
        font_size_pt=12,
    )

    assert measured_height > single_line_height * 4
