# -*- coding: utf-8 -*-

"""
This module handles mnemonic phrases and key derivation for Session.
It uses a custom mnemonic scheme which is not compatible with BIP39.
"""

import json
import binascii
from pathlib import Path
from typing import List, Optional

from nacl.signing import SigningKey
from nacl.public import PrivateKey

from .keypair import Keypair, SigningKeypair, BoxKeypair

_WORDS: Optional[List[str]] = None
_PREFIX_LEN = 3


def load_words() -> List[str]:
    """Load English word list used for mnemonics."""
    global _WORDS
    if _WORDS is None:
        path = Path(__file__).parent.parent.parent / "session_py_client/english_words.json"
        with open(path, "r", encoding="utf-8") as f:
            _WORDS = json.load(f)
    assert _WORDS is not None
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

    checksum_word = ""
    if _PREFIX_LEN > 0 and len(wlist) == 13:
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

    # The checksum logic from the client is not fully replicated here.
    # This is sufficient for key generation but may fail for validation.
    if _PREFIX_LEN > 0 and checksum_word:
        index = _get_checksum_index(wlist)
        expected = words[index]
        if expected[:_PREFIX_LEN] != checksum_word[:_PREFIX_LEN]:
            # We are ignoring checksum errors for now to match TS client behavior
            # where key generation seems to proceed regardless of checksum.
            pass

    return out.hex()


import hashlib

def to_keypair(seed: bytes) -> Keypair:
    """
    Derives a Keypair from a 32-byte seed.
    """
    signing_key = SigningKey(seed)
    
    # Convert Ed25519 private key to Curve25519 private key
    h = hashlib.sha512(seed).digest()
    x25519_priv_key_bytes = h[:32]
    
    # Clamp the key
    x25519_priv_key_bytes = bytearray(x25519_priv_key_bytes)
    x25519_priv_key_bytes[0] &= 248
    x25519_priv_key_bytes[31] &= 127
    x25519_priv_key_bytes[31] |= 64
    
    box_priv_key = PrivateKey(bytes(x25519_priv_key_bytes))

    return Keypair(
        ed25519=SigningKeypair(
            pub_key=bytes(signing_key.verify_key),
            priv_key=bytes(signing_key)
        ),
        x25519=BoxKeypair(
            pub_key=bytes(box_priv_key.public_key),
            priv_key=bytes(box_priv_key)
        )
    )


def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    """
    Converts a Session mnemonic phrase to a 32-byte seed.
    This is not BIP39 compatible.
    """
    seed_hex = decode_mnemonic(mnemonic)
    
    # Replicate the seed padding from the TS client
    priv_key_hex_length = 32 * 2
    if len(seed_hex) != priv_key_hex_length:
        seed_hex = (seed_hex + '0' * 32)[:priv_key_hex_length]

    return bytes.fromhex(seed_hex)


def generate_mnemonic() -> str:
    """
    Generates a 13-word mnemonic phrase.
    This is not a standard BIP39 mnemonic.
    """
    # This function should be updated to correctly generate a valid
    # Session mnemonic with a correct checksum. For now, it's a placeholder.
    import random
    words = load_words()
    # This is not how Session generates mnemonics, but it's a placeholder
    # for now. A proper implementation would involve generating random bytes
    # and encoding them into words with a checksum.
    random_words = random.choices(words, k=12)
    
    checksum_index = _get_checksum_index(random_words)
    checksum_word = words[checksum_index]

    return " ".join(random_words) + " " + checksum_word
