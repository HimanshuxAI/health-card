import math

from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.presentation import Presentation
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

        notes = ""
        if slide.has_notes_slide:
            notes_text_frame = slide.notes_slide.notes_text_frame
            if notes_text_frame is not None:
                notes = notes_text_frame.text.strip()
        if not notes:
            errors.append(f"slide {index}: missing speaker notes")

        slide_element = slide._element
        if slide_element.xpath(".//a:gradFill"):
            errors.append(f"slide {index}: gradient fill is not allowed")
        rounded_rectangles += len(
            slide_element.xpath('.//p:spPr/a:prstGeom[@prst="roundRect"]')
        )

        for shape in slide.shapes:
            angle = math.radians(shape.rotation or 0.0)
            half_width = (
                abs(shape.width * math.cos(angle))
                + abs(shape.height * math.sin(angle))
            ) / 2
            half_height = (
                abs(shape.width * math.sin(angle))
                + abs(shape.height * math.cos(angle))
            ) / 2
            center_x = shape.left + shape.width / 2
            center_y = shape.top + shape.height / 2
            visible_left = center_x - half_width
            visible_top = center_y - half_height
            visible_right = center_x + half_width
            visible_bottom = center_y + half_height

            if visible_left < -tolerance or visible_top < -tolerance:
                errors.append(f"slide {index}: shape starts outside the canvas")
            if visible_right > prs.slide_width + tolerance:
                errors.append(f"slide {index}: shape exceeds the right canvas edge")
            if visible_bottom > prs.slide_height + tolerance:
                errors.append(f"slide {index}: shape exceeds the bottom canvas edge")

        required_pictures = {4: 3, 8: 1}.get(index)
        if required_pictures is not None:
            pictures = sum(
                shape.shape_type == MSO_SHAPE_TYPE.PICTURE for shape in slide.shapes
            )
            if pictures != required_pictures:
                noun = (
                    "project screenshot"
                    if required_pictures == 1
                    else "project screenshots"
                )
                errors.append(
                    f"slide {index}: expected exactly {required_pictures} {noun}, "
                    f"found {pictures}"
                )

    if rounded_rectangles > 4:
        errors.append(
            f"expected at most 4 rounded rectangles, found {rounded_rectangles}"
        )
    return errors
