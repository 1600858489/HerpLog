import hashlib
import secrets


def generate_refresh_token() -> str:
    """Generate a cryptographically secure refresh token value."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token before the authentication service persists it."""
    return hashlib.sha256(token.encode()).hexdigest()
