"""Message encryption helpers using PyNaCl."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, Iterable, List, Optional

from nacl import bindings, public, signing

from ..utils import concatUInt8Array, hexToUint8Array, removePrefixIfNeeded
from .message_padding import add_message_padding


class EnvelopeType(IntEnum):
    """Enumeration of envelope types."""

    SESSION_MESSAGE = 6
    CLOSED_GROUP_MESSAGE = 7


@dataclass
class SodiumKeyPair:
    """Wrapper around a sodium key pair."""

    publicKey: bytes
    privateKey: bytes


@dataclass
class Keypair:
    """Combined X25519 and Ed25519 key pairs."""

    x25519: SodiumKeyPair
    ed25519: SodiumKeyPair


@dataclass
class Envelope:
    """Simple representation of a message envelope."""

    type: EnvelopeType
    source: Optional[str]
    timestamp: int
    content: bytes


def generate_keypair() -> Keypair:
    """
    Generate a new ``Keypair`` using random keys.

    Returns:
        Keypair: Generated key pair with X25519 and Ed25519 keys.
    """

    x_sk = public.PrivateKey.generate()
    ed_sk = signing.SigningKey.generate()
    return Keypair(
        x25519=SodiumKeyPair(
            publicKey=bytes(x_sk.public_key), privateKey=bytes(x_sk)
        ),
        ed25519=SodiumKeyPair(
            publicKey=bytes(ed_sk.verify_key), privateKey=bytes(ed_sk)
        ),
    )


def get_keypair_from_seed(seed_hex: str) -> Keypair:
    """Generate a ``Keypair`` deterministically from a hex seed."""

    priv_key_hex_length = 64
    if len(seed_hex) != priv_key_hex_length:
        seed_hex = (seed_hex + "0" * 32)[:priv_key_hex_length]
    seed = bytes.fromhex(seed_hex)

    pk, sk = bindings.crypto_sign_seed_keypair(seed)
    x_public = bindings.crypto_sign_ed25519_pk_to_curve25519(pk)
    prepended_x_public = b"\x05" + x_public
    x_secret = bindings.crypto_sign_ed25519_sk_to_curve25519(sk)

    return Keypair(
        x25519=SodiumKeyPair(publicKey=prepended_x_public, privateKey=x_secret),
        ed25519=SodiumKeyPair(publicKey=pk, privateKey=sk),
    )


@dataclass
class EncryptResult:
    """Result returned by :func:`encrypt`."""

    envelopeType: EnvelopeType
    cipherText: bytes


def encrypt(
    sender_keypair: Keypair,
    recipient: str,
    plain_text_buffer: bytes,
    encryption_type: EnvelopeType,
) -> EncryptResult:
    """
    Encrypt a plaintext message using the Session protocol.

    Args:
        sender_keypair (Keypair): Our keypair used for signing.
        recipient (str): Recipient Session ID (hex string).
        plain_text_buffer (bytes): Plaintext message to encrypt.
        encryption_type (EnvelopeType): Envelope type to use.

    Returns:
        EncryptResult: Envelope type and ciphertext.
    """

    if encryption_type not in (
        EnvelopeType.CLOSED_GROUP_MESSAGE,
        EnvelopeType.SESSION_MESSAGE,
    ):
        raise ValueError(f"Invalid encryption type: {encryption_type}")

    padded = add_message_padding(plain_text_buffer)

    cipher_text = _encrypt_using_session_protocol(
        sender_keypair, recipient, padded
    )

    return EncryptResult(encryption_type, cipher_text)


def _encrypt_using_session_protocol(
    sender_keypair: Keypair, recipient: str, plaintext: bytes
) -> bytes:
    """
    Perform low level Session encryption steps.

    Args:
        sender_keypair (Keypair): Our keypair used for signing.
        recipient (str): Hex encoded X25519 recipient public key.
        plaintext (bytes): Padded plaintext message.

    Returns:
        bytes: Ciphertext produced by ``crypto_box_seal``.
    """

    ed_priv = sender_keypair.ed25519.privateKey
    ed_pub = sender_keypair.ed25519.publicKey
    if not ed_priv or not ed_pub:
        raise ValueError("Missing Ed25519 keypair")

    recipient_pub = hexToUint8Array(removePrefixIfNeeded(recipient))

    verification_data = concatUInt8Array(plaintext, ed_pub, recipient_pub)
    signature = signing.SigningKey(ed_priv).sign(verification_data).signature

    plaintext_with_meta = concatUInt8Array(plaintext, ed_pub, signature)

    return bindings.crypto_box_seal(plaintext_with_meta, recipient_pub)


def build_envelope(
    type_: EnvelopeType,
    ssk_source: Optional[str],
    timestamp: int,
    content: bytes,
) -> Envelope:
    """
    Build an :class:`Envelope` instance.

    Args:
        type_ (EnvelopeType): Envelope type.
        ssk_source (Optional[str]): Source identity for closed groups.
        timestamp (int): Message timestamp.
        content (bytes): Ciphertext content.

    Returns:
        Envelope: Constructed envelope object.
    """

    source = ssk_source if type_ == EnvelopeType.CLOSED_GROUP_MESSAGE else None
    return Envelope(type=type_, source=source, timestamp=timestamp, content=content)


def _encode_envelope(envelope: Envelope) -> bytes:
    obj = {
        "type": int(envelope.type),
        "source": envelope.source,
        "timestamp": envelope.timestamp,
        "content": base64.b64encode(envelope.content).decode("ascii"),
    }
    return json.dumps(obj).encode()


def wrap_envelope(envelope: Envelope) -> bytes:
    """
    Wrap an :class:`Envelope` into a websocket style container.

    Args:
        envelope (Envelope): Envelope to wrap.

    Returns:
        bytes: Encoded websocket message.
    """

    body = base64.b64encode(_encode_envelope(envelope)).decode("ascii")
    websocket = {
        "type": "REQUEST",
        "request": {
            "id": 0,
            "verb": "PUT",
            "path": "/api/v1/message",
            "body": body,
        },
    }
    return json.dumps(websocket).encode()


class EncryptAndWrapMessage(Dict[str, Any]):
    pass


class EncryptAndWrapMessageResults(Dict[str, Any]):
    pass


def wrap(
    sender_keypair: Keypair,
    messages: Iterable[EncryptAndWrapMessage],
    *,
    network_timestamp: int,
) -> List[EncryptAndWrapMessageResults]:
    """
    Encrypt and wrap multiple messages for sending.

    Args:
        sender_keypair (Keypair): Our keypair used for signing.
        messages (Iterable[EncryptAndWrapMessage]): Messages to process.
        network_timestamp (int): Timestamp to include in envelopes.

    Returns:
        List[EncryptAndWrapMessageResults]: Encoded message descriptors.
    """

    results: List[EncryptAndWrapMessageResults] = []
    for msg in messages:
        destination = msg.get("destination")
        is_group = bool(msg.get("isGroup"))
        plaintext = msg.get("plainTextBuffer", b"")
        namespace = msg.get("namespace")
        ttl = msg.get("ttl")
        identifier = msg.get("identifier")
        sync_message = msg.get("isSyncMessage", False)

        envelope_type = (
            EnvelopeType.CLOSED_GROUP_MESSAGE
            if is_group
            else EnvelopeType.SESSION_MESSAGE
        )
        enc = encrypt(
            sender_keypair,
            destination,
            plaintext,
            envelope_type,
        )
        envelope = build_envelope(
            enc.envelopeType,
            destination if is_group else None,
            network_timestamp,
            enc.cipherText,
        )
        data = wrap_envelope(envelope)
        data64 = base64.b64encode(data).decode("ascii")
        overriden_namespace = (
            namespace
            if namespace is not None
            else (
                -10 if is_group else 0
            )
        )
        results.append(
            {
                "data64": data64,
                "networkTimestamp": network_timestamp,
                "data": data,
                "namespace": overriden_namespace,
                "ttl": ttl,
                "identifier": identifier,
                "isSyncMessage": sync_message,
            }
        )
    return results
