# -*- coding: utf-8 -*-

"""
This module handles setting and getting the mnemonic for a Session instance.
"""

from session_py.errors import SessionRuntimeError, SessionRuntimeErrorCode, SessionValidationError, SessionValidationErrorCode
from session_py.utils import bytes_to_hex
from session_py.crypto.mnemonic import mnemonic_to_seed, to_keypair
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .session import Session


async def set_mnemonic(self: 'Session', mnemonic: str, display_name: Optional[str] = None):
    """
    Sets the mnemonic for this instance, parses it to a keypair.
    """
    if self.is_authorized:
        raise SessionRuntimeError(
            code=SessionRuntimeErrorCode.ALREADY_INITIALIZED,
            message="Mnemonic can't be set after it was already set"
        )
    mnemonic = mnemonic.strip()
    words = mnemonic.split(' ')
    if len(words) != 13:
        raise SessionValidationError(
            code=SessionValidationErrorCode.INVALID_MNEMONIC,
            message=f'Invalid number of words in mnemonic. Expected 13, got {len(words)}'
        )

    seed = mnemonic_to_seed(mnemonic)

    self.keypair = to_keypair(seed)
    self.session_id = f'05{bytes_to_hex(self.keypair.x25519.pub_key)}'
    self.mnemonic = mnemonic

    if display_name:
        self.display_name = display_name
    
    await self.storage.set('mnemonic', mnemonic)
    if display_name:
        await self.storage.set('display_name', display_name)

    self.is_authorized = True
    # We don't start polling here, the user should do it explicitly


def get_mnemonic(self: 'Session') -> Optional[str]:
    """
    Returns the mnemonic of this instance.
    """
    return self.mnemonic
