from uuid import UUID, uuid4


def generate_uuid() -> UUID:
    """Generate a UUID for an externally addressable record."""
    return uuid4()
