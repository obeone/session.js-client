import pytest

from session_py_client.attachments.encrypt import (
    encryptFileAttachment,
    encryptAttachmentData,
    addAttachmentPadding,
)
from session_py_client.attachments.decrypt import decryptAttachment


def test_padding_increases_size():
    data = b"abc"
    padded = addAttachmentPadding(data)
    assert len(padded) >= len(data)
    assert padded.startswith(data)


def test_encrypt_decrypt_roundtrip(tmp_path):
    original = b"hello world"
    file_path = tmp_path / "f.txt"
    file_path.write_bytes(original)

    with open(file_path, "rb") as f:
        enc = encryptFileAttachment(f)

    assert set(enc.keys()) == {"ciphertext", "digest", "key"}

    dec = decryptAttachment(
        enc["ciphertext"],
        size=len(original),
        keyBuffer=enc["key"],
        digestBuffer=enc["digest"],
    )
    assert dec == original


def test_bad_digest_raises(tmp_path):
    original = b"data"
    file_path = tmp_path / "f.bin"
    file_path.write_bytes(original)

    with open(file_path, "rb") as f:
        enc = encryptFileAttachment(f)

    bad_digest = bytearray(enc["digest"])
    bad_digest[0] ^= 0xFF

    with pytest.raises(ValueError):
        decryptAttachment(
            enc["ciphertext"],
            size=len(original),
            keyBuffer=enc["key"],
            digestBuffer=bytes(bad_digest),
        )
