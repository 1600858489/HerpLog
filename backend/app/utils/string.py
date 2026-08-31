def normalize_optional_text(value: str | None) -> str | None:
    """Trim optional text and represent blank input as None."""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
