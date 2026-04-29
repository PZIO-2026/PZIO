import pytest

from pzio.modules.auth.models import UserRole
from pzio.modules.auth.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_produces_different_value() -> None:
    plain = "correct horse battery staple"
    digest = hash_password(plain)
    assert digest != plain
    assert digest.startswith("$2")  # bcrypt prefix


def test_verify_password_accepts_correct_password() -> None:
    plain = "correct horse battery staple"
    digest = hash_password(plain)
    assert verify_password(plain, digest) is True


def test_verify_password_rejects_wrong_password() -> None:
    digest = hash_password("correct horse battery staple")
    assert verify_password("wrong password", digest) is False


def test_verify_password_returns_false_on_malformed_hash() -> None:
    assert verify_password("anything", "not-a-bcrypt-hash") is False


def test_jwt_roundtrip_carries_user_id_and_role() -> None:
    token, expires_in = create_access_token(user_id=42, role=UserRole.TEAM_MEMBER)
    claims = decode_access_token(token)
    assert claims["sub"] == "42"
    assert claims["role"] == UserRole.TEAM_MEMBER.value
    assert expires_in > 0
    assert claims["exp"] > claims["iat"]


def test_decode_access_token_rejects_garbage() -> None:
    with pytest.raises(InvalidTokenError):
        decode_access_token("not.a.jwt")
