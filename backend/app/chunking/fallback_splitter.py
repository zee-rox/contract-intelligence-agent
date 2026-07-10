def split_long_text(text: str, max_chars: int = 1800, overlap: int = 120) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        boundary = text.rfind("\n\n", start, end)
        if boundary <= start:
            boundary = text.rfind(". ", start, end)
        if boundary <= start:
            boundary = end
        part = text[start:boundary].strip()
        if part:
            parts.append(part)
        if boundary >= len(text):
            break
        start = max(boundary - overlap, start + 1)
    return parts
