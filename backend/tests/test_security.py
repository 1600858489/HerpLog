from backend.app.core.security.jwt import create_access_token, decode_access_token
from backend.app.core.security.password import hash_password, verify_password
from backend.app.core.security.token import generate_refresh_token, hash_refresh_token


def test_password_hash_is_verifiable_and_not_plaintext() -> None:
    password_hash = hash_password("correct horse battery staple")
    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong", password_hash)


def test_access_token_round_trip() -> None:
    token = create_access_token("user-uuid")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-uuid"
    assert payload["type"] == "access"


def test_refresh_token_is_random_and_only_hash_is_persisted() -> None:
    token = generate_refresh_token()
    assert token != generate_refresh_token()
    assert hash_refresh_token(token) == hash_refresh_token(token)
    assert hash_refresh_token(token) != token
