from __future__ import annotations

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import PROFILE_IV_LENGTH, PROFILE_KEY_LENGTH, PROFILE_TAG_LENGTH


def decrypt_profile(data: bytes, key: bytes) -> bytes:
    '''
    Decrypt profile data previously encrypted with `encrypt_profile`.

    Args:
        data (bytes): Concatenation of IV and ciphertext with tag.
        key (bytes): Encryption key of length PROFILE_KEY_LENGTH.

    Returns:
        bytes: Decrypted plaintext.
    '''
    min_length = PROFILE_IV_LENGTH + PROFILE_TAG_LENGTH // 8 + 1
    if len(data) < min_length:
        raise ValueError(f"Got too short input: {len(data)}")

    iv = data[:PROFILE_IV_LENGTH]
    ciphertext = data[PROFILE_IV_LENGTH:]
    if len(key) != PROFILE_KEY_LENGTH:
        raise ValueError("Invalid profile key length")
    if len(iv) != PROFILE_IV_LENGTH:
        raise ValueError("Invalid profile iv length")

    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(iv, ciphertext, None)
    except Exception as exc:
        raise ValueError("Failed to decrypt profile data") from exc
