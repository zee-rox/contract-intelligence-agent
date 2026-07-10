import string


def text_quality_score(text: str) -> float:
    stripped = text.strip()
    if not stripped:
        return 0.0
    printable = sum(1 for char in stripped if char in string.printable or char.isprintable())
    alpha_words = [word for word in stripped.split() if any(ch.isalpha() for ch in word)]
    replacement_penalty = stripped.count("\ufffd") / max(len(stripped), 1)
    printable_ratio = printable / max(len(stripped), 1)
    word_score = min(len(alpha_words) / 20, 1.0)
    return max(0.0, min(1.0, (printable_ratio * 0.55) + (word_score * 0.45) - replacement_penalty))


def should_ocr(text: str, quality_score: float) -> tuple[bool, str | None]:
    if not text.strip():
        return True, "empty_native_text"
    if quality_score < 0.35:
        return True, "low_native_text_quality"
    return False, None
