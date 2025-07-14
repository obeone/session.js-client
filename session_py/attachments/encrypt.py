# -*- coding: utf-8 -*-

"""
This module handles the encryption of attachments.
"""

import os
import json
import random
from typing import Union, TYPE_CHECKING
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from session_py.network.base import Request
from session_py.types.attachment import AttachmentPointer
from session_py.utils import bytes_to_base64
import hashlib
from session_py.errors import SessionFetchError, SessionFetchErrorCode

if TYPE_CHECKING:
    from session_py.instance.session import Session


async def encrypt_file(file_path: Union[str, bytes], session: 'Session') -> AttachmentPointer:
    """
    Encrypts a file and prepares it for sending as an attachment.

    :param file_path: Path to the file to encrypt, or bytes of the file.
    :param session: The Session instance to use for uploading the encrypted file.
    :return: An AttachmentPointer instance.
    """
    if isinstance(file_path, str):
        with open(file_path, 'rb') as f:
            plaintext = f.read()
        file_name = os.path.basename(file_path)
    else:
        plaintext = file_path
        file_name = None

    key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    ciphertext = aesgcm.encrypt(iv, plaintext, None)
    digest = hashlib.sha256(ciphertext).digest()

    our_swarm = await session.get_our_swarm()
    if not our_swarm:
        raise SessionFetchError(
            code=SessionFetchErrorCode.SNODE_ERROR,
            message="Could not get a swarm for uploading attachment"
        )

    snode = random.choice(our_swarm.snodes)

    body = {
        "method": "store",
        "params": {
            "pubkey": session.get_session_id(),
            "ttl": "86400",  # 24 hours
            "timestamp": str(session.get_now_with_network_offset()),
            "data": bytes_to_base64(ciphertext)
        }
    }

    req = Request(
        url=f"https://{snode.host}:{snode.port}/storage_rpc/v1",
        method="POST",
        body=json.dumps(body)
    )

    resp = await session.network.on_request(req)

    if resp.status_code != 200:
        raise SessionFetchError(
            code=SessionFetchErrorCode.SNODE_ERROR,
            message=f"Failed to upload attachment: Status code {resp.status_code}, Body: {resp.body}"
        )

    response_json = json.loads(resp.body)
    attachment_id = response_json.get('id')

    return AttachmentPointer(
        identifier=attachment_id,
        size=len(ciphertext),
        key=key,
        iv=iv,
        url=f"https://{snode.host}:{snode.port}/attachments/{attachment_id}",
        digest=digest.hex(),
        file_name=file_name
    )
