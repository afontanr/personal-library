import unicodedata


def normalize_text(text: str) -> str:
    """Lowercase, accent-free, trimmed form used to compare names."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.casefold().strip()
