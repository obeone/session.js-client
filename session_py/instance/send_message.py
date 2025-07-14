# -*- coding: utf-8 -*-

"""
This module handles sending messages.
"""

from typing import TYPE_CHECKING, Optional, List, Dict, Any
from session_py.errors import SessionRuntimeError, SessionRuntimeErrorCode, SessionValidationError, SessionValidationErrorCode
from session_py.utils import is_hex
from session_py.messages.schema.signal import Content, DataMessage
from session_py.crypto.message_encrypt import wrap

if TYPE_CHECKING:
    from .session import Session


async def send_message(
    self: 'Session',
    to: str,
    text: Optional[str] = None,
    attachments: Optional[List[Any]] = None,
    voice_message: Optional[bytes] = None,
    reply_to_message: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Sends a visible chat message to other Session ID.
    """
    if not self.session_id or not self.keypair:
        raise SessionRuntimeError(
            code=SessionRuntimeErrorCode.EMPTY_USER,
            message='Instance is not initialized; use set_mnemonic first'
        )
    if len(to) != 66 or not to.startswith('05') or not is_hex(to.replace('05', '')):
        raise SessionValidationError(
            code=SessionValidationErrorCode.INVALID_SESSION_ID,
            message='Invalid session ID'
        )

    timestamp = int(self.get_now_with_network_offset())
    
    data_message = DataMessage(body=text, timestamp=timestamp)
    content = Content(dataMessage=data_message)
    plain_text_buffer = content.encode()

    raw_message = {'destination': to, 'plainTextBuffer': plain_text_buffer}
    
    wrapped_messages = await wrap(
        sender_keypair=self.keypair,
        messages=[raw_message],
        network_timestamp=timestamp
    )

    message_hash = await self._store_message(
        message=raw_message,
        data=wrapped_messages[0]
    )

    return {
        'messageHash': message_hash,
        'syncMessageHash': 'not_implemented_yet',
        'timestamp': timestamp,
    }
