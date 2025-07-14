# -*- coding: utf-8 -*-

"""
This module provides utilities for signing requests.
"""

import base64
from nacl.signing import SigningKey
from typing import TYPE_CHECKING
from session_py.logs import get_logger

if TYPE_CHECKING:
    from .keypair import Keypair


from session_py.utils import bytes_to_hex

logger = get_logger(__name__)

def sign_request(keypair: 'Keypair', method: str, namespace: int, timestamp: int) -> dict:
    """
    Signs a request for a snode and returns the signature parameters.

    :param keypair: The keypair to sign with.
    :param method: The request method (e.g., 'retrieve').
    :param namespace: The namespace for the request.
    :param timestamp: The current timestamp.
    :return: A dictionary with signature parameters.
    """
    signing_key = SigningKey(keypair.ed25519.priv_key)
    if namespace == 0:
        message_str = f'{method}{timestamp}'
    else:
        message_str = f'{method}{namespace}{timestamp}'
    
    message = message_str.encode('utf-8')
    
    signed = signing_key.sign(message)
    signature = base64.b64encode(signed.signature).decode('utf-8')
    
    return {
        "signature": signature,
        "pubkeyEd25519": bytes_to_hex(keypair.ed25519.pub_key)
    }
