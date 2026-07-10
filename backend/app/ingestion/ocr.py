from pathlib import Path


class OcrUnavailableError(RuntimeError):
    pass


def ocr_pdf_page(pdf_path: Path, page_index: int, language: str, dpi: int) -> str:
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as exc:
        raise OcrUnavailableError("OCR dependencies are not installed") from exc

    images = convert_from_path(str(pdf_path), dpi=dpi, first_page=page_index + 1, last_page=page_index + 1)
    if not images:
        return ""
    return str(pytesseract.image_to_string(images[0], lang=language))
