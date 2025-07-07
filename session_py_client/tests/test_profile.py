import os
import pytest

from session_py_client.profile import (
    PROFILE_IV_LENGTH,
    PROFILE_KEY_LENGTH,
    PROFILE_TAG_LENGTH,
    encrypt_profile,
    decrypt_profile,
)


def test_encrypt_decrypt_roundtrip():
    data = b"test data"
    key = os.urandom(PROFILE_KEY_LENGTH)
    encrypted = encrypt_profile(data, key)
    assert len(encrypted) >= PROFILE_IV_LENGTH + len(data) + PROFILE_TAG_LENGTH // 8
    decrypted = decrypt_profile(encrypted, key)
    assert decrypted == data


def test_invalid_key_length():
    with pytest.raises(ValueError):
        encrypt_profile(b"data", b"short")
    with pytest.raises(ValueError):
        decrypt_profile(b"\x00" * (PROFILE_IV_LENGTH + PROFILE_TAG_LENGTH // 8 + 1), b"short")


def test_too_short_input():
    key = os.urandom(PROFILE_KEY_LENGTH)
    with pytest.raises(ValueError):
        decrypt_profile(b"\x00" * (PROFILE_IV_LENGTH + PROFILE_TAG_LENGTH // 8), key)
