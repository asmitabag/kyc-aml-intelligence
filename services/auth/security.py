import hashlib
import hmac
import secrets


SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
KEY_BYTES = 32


def hash_password(password: str) -> str:
    if not password or len(password) < 8:
        raise ValueError("Password must contain at least 8 characters")

    if len(password.encode("utf-8")) > 1024:
        raise ValueError("Password is too long")

    salt = secrets.token_bytes(SALT_BYTES)
    derived_key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=KEY_BYTES,
    )

    return (
        f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}"
        f"${salt.hex()}${derived_key.hex()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, n, r, p, salt_hex, key_hex = stored_hash.split("$")

        if algorithm != "scrypt":
            return False

        n, r, p = int(n), int(r), int(p)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)

        # Reject malformed or unexpectedly expensive stored parameters.
        if (
            n != SCRYPT_N
            or r != SCRYPT_R
            or p != SCRYPT_P
            or len(salt) != SALT_BYTES
            or len(expected_key) != KEY_BYTES
        ):
            return False

        actual_key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(expected_key),
        )

        return hmac.compare_digest(actual_key, expected_key)

    except (ValueError, TypeError, AttributeError):
        return False