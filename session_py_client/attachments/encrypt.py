"""Attachment encryption utilities."""

from __future__ import annotations

from typing import BinaryIO, Dict
from math import ceil, log, pow

from nacl.utils import random as nacl_random
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac, padding

PADDING_BYTE = 0x00
MAX_ATTACHMENT_FILESIZE_BYTES = 10 * 1000 * 1000


def addAttachmentPadding(data: bytes) -> bytes:
    """Add padding to attachment data to obscure its real size."""

    original_len = len(data)
    padded_size = max(
        541,
        int(pow(1.05, ceil(log(max(original_len, 1), 1.05)))),
    )
    if padded_size > MAX_ATTACHMENT_FILESIZE_BYTES and original_len <= MAX_ATTACHMENT_FILESIZE_BYTES:
        padded_size = MAX_ATTACHMENT_FILESIZE_BYTES
    padding_len = padded_size - original_len
    return data + bytes([PADDING_BYTE]) * padding_len


def encryptFileAttachment(file_obj: BinaryIO) -> Dict[str, bytes]:
    """Encrypt a file attachment using random keys."""

    data = file_obj.read()
    return encryptAttachment(data, add_padding=True)


def encryptAttachment(data: bytes, add_padding: bool = False) -> Dict[str, bytes]:
    """Encrypt attachment bytes and return ciphertext, digest and key."""

    pointer_key = nacl_random(64)
    iv = nacl_random(16)
    padded = addAttachmentPadding(data) if add_padding else data
    encrypted = encryptAttachmentData(padded, pointer_key, iv)
    encrypted["key"] = pointer_key
    return encrypted


def encryptAttachmentData(plaintext: bytes, keys: bytes, iv: bytes) -> Dict[str, bytes]:
    """Encrypt attachment data using AES-CBC and HMAC-SHA256."""

    if len(keys) != 64:
        raise ValueError("Got invalid length attachment keys")
    if len(iv) != 16:
        raise ValueError("Got invalid length attachment iv")

    aes_key = keys[:32]
    mac_key = keys[32:]

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    iv_and_ciphertext = iv + ciphertext
    h = hmac.HMAC(mac_key, hashes.SHA256())
    h.update(iv_and_ciphertext)
    mac = h.finalize()

    encrypted_bin = iv_and_ciphertext + mac
    digest = hashes.Hash(hashes.SHA256())
    digest.update(encrypted_bin)
    return {
        "ciphertext": encrypted_bin,
        "digest": digest.finalize(),
    }
