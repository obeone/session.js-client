"""Mnemonic utilities for Session tests."""

from __future__ import annotations

import json
import binascii
import secrets
from pathlib import Path
from typing import List

_WORDS: List[str] | None = None
_PREFIX_LEN = 3


def load_words() -> List[str]:
    """Load English word list used for mnemonics."""
    global _WORDS
    if _WORDS is None:
        path = Path(__file__).with_name("english_words.json")
        with open(path, "r", encoding="utf-8") as f:
            _WORDS = json.load(f)
    return _WORDS


def _swap_endian_4byte(hex_str: str) -> str:
    """Swap endianess of an 8 character hex string."""
    if len(hex_str) != 8:
        raise ValueError("Invalid input length")
    return hex_str[6:8] + hex_str[4:6] + hex_str[2:4] + hex_str[0:2]


def _get_checksum_index(words: List[str]) -> int:
    """Return index for checksum word calculation."""
    trimmed = ''.join(w[:_PREFIX_LEN] for w in words)
    crc = binascii.crc32(trimmed.encode()) & 0xFFFFFFFF
    return crc % len(words)


def decode_mnemonic(mnemonic: str) -> str:
    """Decode 13-word mnemonic to seed hex string."""
    words = load_words()
    n = len(words)
    wlist = mnemonic.split()
    if len(wlist) < 12:
        raise ValueError("Invalid number of words")
    if _PREFIX_LEN == 0 and len(wlist) % 3 != 0 or _PREFIX_LEN > 0 and len(wlist) % 3 == 2:
        raise ValueError("Invalid number of words")
    if _PREFIX_LEN > 0 and len(wlist) % 3 == 0:
        raise ValueError("Missing checksum word")
    checksum_word = ""
    if _PREFIX_LEN > 0:
        checksum_word = wlist.pop()
    trunc_words = [w[:_PREFIX_LEN] for w in words]
    out = bytearray()
    for i in range(0, len(wlist), 3):
        if _PREFIX_LEN == 0:
            w1 = words.index(wlist[i])
            w2 = words.index(wlist[i + 1])
            w3 = words.index(wlist[i + 2])
        else:
            w1 = trunc_words.index(wlist[i][:_PREFIX_LEN])
            w2 = trunc_words.index(wlist[i + 1][:_PREFIX_LEN])
            w3 = trunc_words.index(wlist[i + 2][:_PREFIX_LEN])
        if w1 == -1 or w2 == -1 or w3 == -1:
            raise ValueError("Invalid word in mnemonic")
        x = w1 + n * ((n - w1 + w2) % n) + n * n * ((n - w2 + w3) % n)
        if x % n != w1:
            raise ValueError("Couldn't decode mnemonic")
        out.extend(bytes.fromhex(_swap_endian_4byte(f"{x:08x}")))
    if _PREFIX_LEN > 0:
        index = _get_checksum_index(wlist)
        expected = wlist[index][:_PREFIX_LEN]
        if expected != checksum_word[:_PREFIX_LEN]:
            raise ValueError("Invalid checksum word")
    return out.hex()


def generate_mnemonic(num_words: int = 12) -> str:
    """Generate a random mnemonic with checksum."""

    if num_words < 12 or num_words % 3 != 0:
        raise ValueError("num_words must be a multiple of 3 and at least 12")

    words = load_words()
    chosen = [secrets.choice(words) for _ in range(num_words)]

    index = _get_checksum_index(chosen)
    prefix = chosen[index][:_PREFIX_LEN]
    checksum = next((w for w in words if w.startswith(prefix)), chosen[index])

    return " ".join(chosen + [checksum])
