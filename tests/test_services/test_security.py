# tests/test_services/test_security.py
"""
Unit tests for app.core.security.
Pure Python — no database, no HTTP.
"""
import time

import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_returns_string(self):
        h = hash_password("mypassword")
        assert isinstance(h, str)

    def test_hash_is_not_plaintext(self):
        h = hash_password("mypassword")
        assert h != "mypassword"

    def test_correct_password_verifies(self):
        plain = "secure_password_123!"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_empty_password_hashes(self):
        """Edge case: empty string should still hash (policy enforcement is upstream)."""
        h = hash_password("")
        assert isinstance(h, str)

    def test_hashes_are_unique_per_call(self):
        """Argon2 uses random salts; same password must yield different hashes."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2

    def test_verify_against_different_hash_fails(self):
        h = hash_password("password_a")
        assert verify_password("password_b", h) is False


class TestJWT:
    def test_create_returns_non_empty_string(self):
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_returns_subject(self):
        subject = "user-abc-456"
        token = create_access_token(subject)
        decoded = decode_token(token)
        assert decoded == subject

    def test_decode_uuid_subject(self):
        import uuid
        uid = str(uuid.uuid4())
        token = create_access_token(uid)
        assert decode_token(token) == uid

    def test_decode_invalid_token_raises(self):
        import jwt
        with pytest.raises(jwt.InvalidTokenError):
            decode_token("not.a.valid.jwt")

    def test_decode_tampered_signature_raises(self):
        import jwt
        token = create_access_token("user-xyz")
        # Corrupt the last few characters of the signature
        tampered = token[:-8] + "XXXXXXXX"
        with pytest.raises(jwt.InvalidTokenError):
            decode_token(tampered)

    def test_decode_wrong_key_raises(self):
        """A token signed with a different key must be rejected."""
        import jwt
        from app.core.config import settings
        # Sign with a different secret
        fake_token = jwt.encode(
            {"sub": "evil-user", "exp": int(time.time()) + 3600},
            "wrong-secret-key",
            algorithm=settings.ALGORITHM,
        )
        with pytest.raises(jwt.InvalidTokenError):
            decode_token(fake_token)
