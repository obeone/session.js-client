# -*- coding: utf-8 -*-

"""
This module handles message decryption for Session.py.
"""

from typing import Optional
import nacl.secret
from nacl.public import PrivateKey, PublicKey, Box
from nacl.signing import VerifyKey
from nacl.exceptions import CryptoError

from session_py.crypto.keypair import Keypair
from session_py.messages.schema.signal import Signal as Envelope
from session_py.utils import hex_to_bytes, concat_bytes
from session_py.errors import SessionCryptoError, SessionCryptoErrorCode


def decrypt(
    recipient_keypair: Keypair,
    ciphertext: bytes,
    envelope_type: Envelope.Type,
    sender_x25519_pubkey_hex: Optional[str] = None,
    group_id: Optional[str] = None
) -> bytes:
    """
    Decrypts a message using the Session protocol.

    Parameters:
    - recipient_keypair (Keypair): The recipient's keypair.
    - ciphertext (bytes): The encrypted message.
    - envelope_type (Envelope.Type): The type of encryption used.
    - sender_x25519_pubkey_hex (str, optional): The sender's public key for session messages.
    - group_id (str, optional): The group ID for group messages.

    Returns:
    - bytes: The decrypted plaintext.
    """
    if envelope_type == Envelope.Type.SESSION_MESSAGE:
        if not sender_x25519_pubkey_hex:
            raise ValueError("sender_x25519_pubkey_hex is required for SESSION_MESSAGE decryption")
        return _decrypt_session_message(recipient_keypair, sender_x25519_pubkey_hex, ciphertext)
    elif envelope_type == Envelope.Type.CLOSED_GROUP_MESSAGE:
        if not group_id:
            raise ValueError("group_id is required for CLOSED_GROUP_MESSAGE decryption")
        return _decrypt_group_message(group_id, ciphertext)
    else:
        raise SessionCryptoError(
            code=SessionCryptoErrorCode.MESSAGE_DECRYPTION_FAILED,
            message=f"Invalid encryption type: {envelope_type}"
        )


def _decrypt_session_message(
    recipient_keypair: Keypair,
    sender_x25519_pubkey_hex: str,
    ciphertext: bytes
) -> bytes:
    """
    Decrypts a message encrypted with the Session protocol.
    """
    recipient_box_priv_key = PrivateKey(recipient_keypair.x25519.priv_key)
    sender_pub_key_bytes = hex_to_bytes(sender_x25519_pubkey_hex)
    sender_pub_key = PublicKey(sender_pub_key_bytes)

    box = Box(recipient_box_priv_key, sender_pub_key)

    try:
        plaintext_with_metadata = box.decrypt(ciphertext)
    except CryptoError:
        raise SessionCryptoError(
            code=SessionCryptoErrorCode.MESSAGE_DECRYPTION_FAILED,
            message="Failed to decrypt message."
        )

    # Based on encryption: plaintext_with_metadata = plaintext + sender_ed25519_pub_key + signature
    signature = plaintext_with_metadata[-64:]
    sender_ed25519_pub_key_bytes = plaintext_with_metadata[-96:-64]
    padded_plaintext = plaintext_with_metadata[:-96]

    # Verify signature
    verify_key = VerifyKey(sender_ed25519_pub_key_bytes)
    
    verification_data = concat_bytes(
        padded_plaintext,
        sender_ed25519_pub_key_bytes,
        recipient_keypair.x25519.pub_key
    )

    try:
        verify_key.verify(verification_data, signature)
    except CryptoError:
        raise SessionCryptoError(
            code=SessionCryptoErrorCode.MESSAGE_DECRYPTION_FAILED,
            message="Signature verification failed."
        )

    # Extract original length and strip padding
    original_len = int.from_bytes(padded_plaintext[:2], 'big')
    return padded_plaintext[2:2 + original_len]


def _decrypt_group_message(
    group_id: str,
    ciphertext: bytes
) -> bytes:
    """
    Decrypts a message encrypted for a group.
    """
    group_key = hex_to_bytes(group_id)
    box = nacl.secret.SecretBox(group_key)

    try:
        message_with_metadata = box.decrypt(ciphertext)
    except CryptoError:
        raise SessionCryptoError(
            code=SessionCryptoErrorCode.MESSAGE_DECRYPTION_FAILED,
            message="Failed to decrypt group message."
        )

    # Based on encryption: message_with_metadata = sender_ed25519_pub_key + signature + plaintext
    sender_ed25519_pub_key = message_with_metadata[:32]
    signature = message_with_metadata[32:96]
    padded_plaintext = message_with_metadata[96:]

    # Verify signature
    verify_key = VerifyKey(sender_ed25519_pub_key)
    try:
        verify_key.verify(padded_plaintext, signature)
    except CryptoError:
        raise SessionCryptoError(
            code=SessionCryptoErrorCode.MESSAGE_DECRYPTION_FAILED,
            message="Group message signature verification failed."
        )

    # Extract original length and strip padding
    original_len = int.from_bytes(padded_plaintext[:2], 'big')
    return padded_plaintext[2:2 + original_len]
