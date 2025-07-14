# -*- coding: utf-8 -*-

"""
This module handles the decryption of attachments.
"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from typing import TYPE_CHECKING
from session_py.network.base import Request
from session_py.types.attachment import AttachmentPointer
from session_py.errors import SessionFetchError, SessionFetchErrorCode, SessionCryptoError, SessionCryptoErrorCode

if TYPE_CHECKING:
    from session_py.instance.session import Session


async def decrypt(pointer: AttachmentPointer, session: 'Session') -> bytes:
    """
    Downloads and decrypts an attachment.

    :param pointer: The AttachmentPointer to the attachment.
    :param session: The Session instance to use for downloading the attachment.
    :return: The decrypted plaintext of the attachment.
    """
    try:
        response = await session.network.on_request(Request(
            method='GET',
            url=pointer.url
        ))
    except Exception as e:
        raise SessionFetchError(
            code=SessionFetchErrorCode.SNODE_ERROR,
            message=f"Failed to download attachment: {e}"
        )

    if response.status_code != 200:
        raise SessionFetchError(
            code=SessionFetchErrorCode.SNODE_ERROR,
            message=f"Failed to download attachment: {response.status_code}"
        )

    ciphertext = response.body
    aesgcm = AESGCM(pointer.key)
    try:
        plaintext = aesgcm.decrypt(pointer.iv, ciphertext, None)
    except InvalidTag:
        raise SessionCryptoError(
            code=SessionCryptoErrorCode.MESSAGE_DECRYPTION_FAILED,
            message="Failed to decrypt attachment: Invalid authentication tag."
        )

    return plaintext
