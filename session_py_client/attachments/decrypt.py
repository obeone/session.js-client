"""Attachment decryption utilities."""

from __future__ import annotations

from typing import Optional

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac, padding
import hmac as py_hmac


def decryptAttachment(
    data: bytes,
    *,
    size: Optional[int] = None,
    keyBuffer: bytes,
    digestBuffer: bytes,
) -> bytes:
    """Decrypt attachment data verifying MAC and digest."""

    if len(keyBuffer) != 64:
        raise ValueError("Got invalid length attachment keys")
    if len(data) < 16 + 32:
        raise ValueError("Got invalid length attachment")

    aes_key = keyBuffer[:32]
    mac_key = keyBuffer[32:]
    iv = data[:16]
    ciphertext = data[16:-32]
    iv_and_ciphertext = data[:-32]
    mac = data[-32:]

    _verify_mac(iv_and_ciphertext, mac_key, mac)
    _verify_digest(data, digestBuffer)

    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    decrypted_data = unpadder.update(padded) + unpadder.finalize()

    if size is not None and size != len(data):
        if size < len(data):
            decrypted_data = decrypted_data[:size]
        else:
            raise ValueError("Decrypted attachment size does not match expected size")

    return decrypted_data


def _verify_mac(data: bytes, key: bytes, mac: bytes) -> None:
    """Validate HMAC of attachment data."""

    h = hmac.HMAC(key, hashes.SHA256())
    h.update(data)
    calculated = h.finalize()
    if not py_hmac.compare_digest(calculated[: len(mac)], mac):
        raise ValueError("Bad attachment MAC")


def _verify_digest(data: bytes, digest_value: bytes) -> None:
    """Validate SHA-256 digest of encrypted attachment."""

    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    calculated = digest.finalize()
    if not py_hmac.compare_digest(calculated[: len(digest_value)], digest_value):
        raise ValueError("Bad attachment digest")
