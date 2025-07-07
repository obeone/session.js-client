"""Message padding utilities compatible with the JS client."""

from __future__ import annotations


PADDING_BYTE = 0x00


def remove_message_padding(padded_plaintext: bytes) -> bytes:
    """
    Remove padding bytes from a padded message.

    Args:
        padded_plaintext (bytes): Padded plaintext as returned by
            ``add_message_padding``.

    Returns:
        bytes: Original message without padding.

    Raises:
        ValueError: If padding markers are invalid.
    """
    for i in range(len(padded_plaintext) - 1, -1, -1):
        value = padded_plaintext[i]
        if value == 0x80:
            return padded_plaintext[:i]
        if value != PADDING_BYTE:
            return padded_plaintext
    raise ValueError("Invalid padding")


def add_message_padding(message: bytes) -> bytes:
    """
    Add padding bytes according to Session message rules.

    Args:
        message (bytes): Plaintext message to pad.

    Returns:
        bytes: Padded message ready for encryption.
    """
    padded_len = _get_padded_message_length(len(message) + 1) - 1
    plaintext = bytearray(padded_len)
    plaintext[: len(message)] = message
    plaintext[len(message)] = 0x80
    return bytes(plaintext)


def _get_padded_message_length(original_length: int) -> int:
    message_length_with_terminator = original_length + 1
    message_part_count = message_length_with_terminator // 160
    if message_length_with_terminator % 160 != 0:
        message_part_count += 1
    return message_part_count * 160
