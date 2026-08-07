"""Unit tests for auth helpers — no external services required."""

from jose import jwt

from core.config import settings
from core.security import create_access_token, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-pass")
    assert hashed != "s3cret-pass"
    assert verify_password("s3cret-pass", hashed)
    assert not verify_password("wrong-pass", hashed)


def test_access_token_roundtrip():
    token = create_access_token(subject="alice")
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["sub"] == "alice"
    assert "exp" in payload
