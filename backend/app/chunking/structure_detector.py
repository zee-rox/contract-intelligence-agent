import re

HEADING_PATTERN = re.compile(
    r"^\s*((?i:section\s+\d+(?:\.\d+)*)|(?i:article\s+[ivxlcdm]+)|(?:\d+(?:\.\d+)*\.?)|(?:\([a-zivx]+\))|[A-Z][A-Z \-]{3,})\s*(.*)$",
)

COMMON_HEADINGS = {
    "termination",
    "confidentiality",
    "governing law",
    "indemnification",
    "limitation of liability",
    "liability",
    "payment",
    "payment terms",
    "force majeure",
}


def detect_heading(line: str) -> str | None:
    stripped = line.strip().rstrip(":")
    if not stripped:
        return None
    lowered = stripped.lower()
    if lowered in COMMON_HEADINGS:
        return stripped
    match = HEADING_PATTERN.match(stripped)
    if not match:
        return None
    remainder = match.group(2).strip()
    return remainder or stripped
