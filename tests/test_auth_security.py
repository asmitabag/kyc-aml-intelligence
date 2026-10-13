import pytest

from services.auth.security import hash_password, verify_password


def test_password_hash_is_not_plaintext():
    password = "ExamplePassword123!"
    stored_hash = hash_password(password)

    assert password not in stored_hash
    assert stored_hash.startswith("scrypt$")


def test_password_verification_succeeds():
    password = "ExamplePassword123!"
    stored_hash = hash_password(password)

    assert verify_password(password, stored_hash)


def test_wrong_password_is_rejected():
    stored_hash = hash_password("ExamplePassword123!")

    assert not verify_password("WrongPassword123!", stored_hash)


def test_same_password_gets_different_salts():
    password = "ExamplePassword123!"

    assert hash_password(password) != hash_password(password)


def test_short_password_is_rejected():
    with pytest.raises(ValueError):
        hash_password("short")