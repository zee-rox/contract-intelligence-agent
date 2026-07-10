from app.ingestion.quality import should_ocr, text_quality_score


def test_ocr_fallback_is_selective() -> None:
    clean = "This Agreement contains payment terms and termination rights."
    clean_score = text_quality_score(clean)
    assert should_ocr(clean, clean_score) == (False, None)

    use_ocr, reason = should_ocr("", text_quality_score(""))
    assert use_ocr is True
    assert reason == "empty_native_text"
