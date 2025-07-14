# -*- coding: utf-8 -*-

"""
This module handles message encryption for Session.py.
"""

import secrets
from typing import List, Dict, Any, NamedTuple
import nacl.secret
from nacl.public import PrivateKey, PublicKey, Box
from nacl.signing import SigningKey
from session_py.crypto.keypair import Keypair
from session_py.utils import hex_to_bytes, remove_prefix_if_needed, concat_bytes, bytes_to_base64
from session_py.errors import SessionCryptoError, SessionCryptoErrorCode
from session_py.messages.schema.signal import Signal as Envelope, Content, DataMessage, encode as encode_envelope
from session_py.types.namespaces import SnodeNamespaces


class EncryptResult(NamedTuple):
    """
    Represents the result of an encryption operation.
    """
    envelope_type: Envelope.Type
    cipher_text: bytes


def add_message_padding(plain_text_buffer: bytes) -> bytes:
    """
    Adds random padding to a message buffer to obscure its true length.

    The padding size is chosen to align the message to a block size of 16, 32, 64, or 128 bytes,
    with a maximum padding of 256 bytes.

    Parameters:
    - plain_text_buffer (bytes): The original message bytes.

    Returns:
    - bytes: The padded message bytes.
    """
    original_length = len(plain_text_buffer)
    padding_length = 0

    if original_length < 128:
        padding_length = (16 - (original_length % 16)) % 16
    elif original_length < 256:
        padding_length = (32 - (original_length % 32)) % 32
    elif original_length < 512:
        padding_length = (64 - (original_length % 64)) % 64
    elif original_length < 1024:
        padding_length = (128 - (original_length % 128)) % 128
    else:
        padding_length = (256 - (original_length % 256)) % 256

    if padding_length == 0:
        padding_length = 16  # Add at least some padding

    padding = secrets.token_bytes(padding_length)
    return plain_text_buffer + padding


async def encrypt(
    sender_keypair: Keypair,
    recipient: str,
    plain_text_buffer: bytes,
    encryption_type: Envelope.Type
) -> EncryptResult:
    """
    Encrypts a message using the Session protocol.

    Parameters:
    - sender_keypair (Keypair): The sender's keypair.
    - recipient (str): The recipient's public key in hex format.
    - plain_text_buffer (bytes): The plaintext message.
    - encryption_type (Envelope.Type): The type of encryption to use.

    Returns:
    - EncryptResult: An object containing the envelope type and ciphertext.
    """
    if encryption_type not in [Envelope.Type.SESSION_MESSAGE, Envelope.Type.CLOSED_GROUP_MESSAGE]:
        raise SessionCryptoError(
            code=SessionCryptoErrorCode.MESSAGE_ENCRYPTION_FAILED,
            message=f"Invalid encryption type: {encryption_type}"
        )

    # Prepend the original length to the plaintext before padding
    len_bytes = len(plain_text_buffer).to_bytes(2, 'big')
    plain_text_with_len = len_bytes + plain_text_buffer
    plain_text = add_message_padding(plain_text_with_len)

    if encryption_type == Envelope.Type.CLOSED_GROUP_MESSAGE:
        # The recipient is the group ID, which is used as a shared secret for encryption.
        # A real implementation would use a proper group key management protocol.
        cipher_text = await _encrypt_for_group(sender_keypair, recipient, plain_text)
        return EncryptResult(envelope_type=Envelope.Type.CLOSED_GROUP_MESSAGE, cipher_text=cipher_text)

    cipher_text = await _encrypt_using_session_protocol(sender_keypair, recipient, plain_text)
    return EncryptResult(envelope_type=Envelope.Type.SESSION_MESSAGE, cipher_text=cipher_text)


async def _encrypt_using_session_protocol(
    sender_keypair: Keypair,
    recipient: str,
    plaintext: bytes
) -> bytes:
    """
    Encrypts a message using the core Session protocol with NaCl Box.
    """
    if not sender_keypair.ed25519.priv_key or not sender_keypair.ed25519.pub_key:
        raise SessionCryptoError(
            code=SessionCryptoErrorCode.MESSAGE_ENCRYPTION_FAILED,
            message="User's Ed25519 key pair is missing."
        )

    recipient_x25519_pub_key_bytes = remove_prefix_if_needed(hex_to_bytes(recipient))

    verification_data = concat_bytes(
        plaintext,
        sender_keypair.ed25519.pub_key,
        recipient_x25519_pub_key_bytes
    )

    signing_key = SigningKey(sender_keypair.ed25519.priv_key)
    signature = signing_key.sign(verification_data).signature
    if not signature:
        raise SessionCryptoError(
            code=SessionCryptoErrorCode.MESSAGE_ENCRYPTION_FAILED,
            message="Couldn't sign message."
        )

    plaintext_with_metadata = concat_bytes(
        plaintext,
        sender_keypair.ed25519.pub_key,
        signature
    )

    sender_box_priv_key = PrivateKey(sender_keypair.x25519.priv_key)
    recipient_pub_key = PublicKey(recipient_x25519_pub_key_bytes)
    box = Box(sender_box_priv_key, recipient_pub_key)

    ciphertext = box.encrypt(plaintext_with_metadata)
    return ciphertext


async def _encrypt_for_group(
    sender_keypair: Keypair,
    group_id: str,
    plaintext: bytes
) -> bytes:
    """
    Encrypts a message for a group using a shared secret.
    For simplicity, the group_id is used as the shared secret.
    A real implementation would use a proper group key management protocol.
    """
    if not sender_keypair.ed25519.priv_key or not sender_keypair.ed25519.pub_key:
        raise SessionCryptoError(
            code=SessionCryptoErrorCode.MESSAGE_ENCRYPTION_FAILED,
            message="User's Ed25519 key pair is missing."
        )

    # The group_id is treated as a hex-encoded shared secret.
    group_key = hex_to_bytes(group_id)

    # Sign the plaintext to prove sender identity.
    signing_key = SigningKey(sender_keypair.ed25519.priv_key)
    signature = signing_key.sign(plaintext).signature

    # Prepend sender's public key and signature to the plaintext.
    message_with_metadata = concat_bytes(
        sender_keypair.ed25519.pub_key,
        signature,
        plaintext
    )

    # Symmetrically encrypt the message with the group key.
    box = nacl.secret.SecretBox(group_key)
    return box.encrypt(message_with_metadata)


class EncryptAndWrapMessage(NamedTuple):
    """
    Represents a message to be encrypted and wrapped.
    """
    destination: str
    plain_text_buffer: bytes
    ttl: int
    identifier: str
    is_sync_message: bool
    is_group: bool
    namespace: int


class EncryptAndWrapMessageResults(NamedTuple):
    """
    Represents the result of encrypting and wrapping a message.
    """
    data64: str
    network_timestamp: int
    data: bytes
    namespace: int
    ttl: int
    identifier: str
    is_sync_message: bool


async def wrap(
    sender_keypair: Keypair,
    messages: List[Dict[str, Any]],
    network_timestamp: int
) -> List[Dict[str, Any]]:
    """
    Encrypts and wraps multiple messages for sending.
    """
    results = []
    for msg in messages:
        # We only support basic text messages for now
        plain_text_buffer = msg['plainTextBuffer']
        destination = msg['destination']

        overridden_buffer = _overwrite_timestamp(plain_text_buffer, network_timestamp, False)

        encrypted = await encrypt(
            sender_keypair,
            destination,
            overridden_buffer,
            Envelope.Type.SESSION_MESSAGE
        )

        envelope = _build_envelope(
            encrypted.envelope_type,
            destination,
            network_timestamp,
            encrypted.cipher_text
        )

        data = _wrap_envelope(envelope)
        data64 = bytes_to_base64(data)

        results.append({
            'data64': data64,
            'destination': destination,
            'ttl': 86400 * 1000,  # 1 day
            'namespace': SnodeNamespaces.UserMessages,
        })
    return results


def _overwrite_timestamp(plain_text_buffer: bytes, network_timestamp: int, is_sync_message: bool) -> bytes:
    """
    Overwrites the timestamp in a message with the network timestamp.
    """
    content = Content.decode(plain_text_buffer)

    if content.dataMessage and content.dataMessage.timestamp > 0:
        if not is_sync_message:
            content.dataMessage.timestamp = network_timestamp

    return content.encode()


def _build_envelope(
    envelope_type: Envelope.Type,
    ssk_source: str,
    timestamp: int,
    content: bytes
) -> Envelope:
    """
    Builds a message envelope.
    """
    source = ssk_source if envelope_type == Envelope.Type.CLOSED_GROUP_MESSAGE else None
    return Envelope(
        type=envelope_type,
        source=source,
        timestamp=timestamp,
        content=content
    )


def _wrap_envelope(envelope: Envelope) -> bytes:
    """
    Wraps an envelope in a WebSocket message structure.
    """
    # This part is a placeholder as WebSocket messages are not fully implemented yet.
    # In a real scenario, this would construct a WebSocket message.
    return encode_envelope(envelope)
