from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

from deck.content import SLIDES


def validate_presentation(prs: Presentation) -> list[str]:
    errors: list[str] = []
    slides = list(prs.slides)
    if len(slides) != 10:
        errors.append(f"expected 10 slides, found {len(slides)}")

    tolerance = Inches(0.01)
    rounded_rectangles = 0

    for index, slide in enumerate(slides, start=1):
        texts = [shape.text for shape in slide.shapes if hasattr(shape, "text")]
        if index <= len(SLIDES) and SLIDES[index - 1].title not in texts:
            errors.append(f"slide {index}: missing approved title")

        notes_text_frame = slide.notes_slide.notes_text_frame
        notes = notes_text_frame.text.strip() if notes_text_frame is not None else ""
        if not notes:
            errors.append(f"slide {index}: missing speaker notes")

        slide_xml = slide._element.xml
        if "<a:gradFill" in slide_xml:
            errors.append(f"slide {index}: gradient fill is not allowed")
        rounded_rectangles += slide_xml.count('prst="roundRect"')

        for shape in slide.shapes:
            if shape.left < -tolerance or shape.top < -tolerance:
                errors.append(f"slide {index}: shape starts outside the canvas")
            if shape.left + shape.width > prs.slide_width + tolerance:
                errors.append(f"slide {index}: shape exceeds the right canvas edge")
            if shape.top + shape.height > prs.slide_height + tolerance:
                errors.append(f"slide {index}: shape exceeds the bottom canvas edge")

        if index in (4, 8):
            pictures = sum(
                shape.shape_type == MSO_SHAPE_TYPE.PICTURE for shape in slide.shapes
            )
            if pictures == 0:
                errors.append(f"slide {index}: required project screenshot is missing")

    if rounded_rectangles > 4:
        errors.append(
            f"expected at most 4 rounded rectangles, found {rounded_rectangles}"
        )
    return errors
