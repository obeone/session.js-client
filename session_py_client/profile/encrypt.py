from __future__ import annotations

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import PROFILE_IV_LENGTH, PROFILE_KEY_LENGTH


def encrypt_profile(data: bytes, key: bytes) -> bytes:
    '''
    Encrypt profile data using AES-GCM.

    Args:
        data (bytes): Plain profile data to encrypt.
        key (bytes): Encryption key of length PROFILE_KEY_LENGTH.

    Returns:
        bytes: IV prepended to the encrypted data and tag.
    '''
    if len(key) != PROFILE_KEY_LENGTH:
        raise ValueError("Invalid profile key length")

    iv = os.urandom(PROFILE_IV_LENGTH)
    if len(iv) != PROFILE_IV_LENGTH:
        raise ValueError("Invalid IV length generated")

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, data, None)
    return iv + ciphertext
