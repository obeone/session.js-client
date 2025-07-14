# -*- coding: utf-8 -*-

"""
This module defines the Keypair types for Session.py.
"""

from dataclasses import dataclass

@dataclass
class SigningKeypair:
    """Represents a public/private keypair for signing (ed25519)."""
    pub_key: bytes
    priv_key: bytes

@dataclass
class BoxKeypair:
    """Represents a public/private keypair for encryption (x25519)."""
    pub_key: bytes
    priv_key: bytes

@dataclass
class Keypair:
    """
    Represents the set of keypairs for a Session identity.
    """
    ed25519: SigningKeypair
    x25519: BoxKeypair

    @property
    def pubkey_hex(self) -> str:
        """
        Returns the hex-encoded public key for the x25519 keypair.
        """
        from session_py.utils import bytes_to_hex
        return bytes_to_hex(self.x25519.pub_key)
