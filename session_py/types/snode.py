# -*- coding: utf-8 -*-

"""
This module defines the Snode type for Session.py.
"""

from dataclasses import dataclass

@dataclass
class Snode:
    """
    Represents a Session node.
    """
    host: str
    port: int
    pubkey_x25519: str
    pubkey_ed25519: str
