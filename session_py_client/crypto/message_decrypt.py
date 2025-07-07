"""Message decryption helpers using PyNaCl."""

from __future__ import annotations

import base64
import json
import time
import uuid
from dataclasses import dataclass
from typing import Iterable, List, Optional

from nacl import bindings, signing

from ..utils import (
    Uint8ArrayToHex,
    base64ToUint8Array,
    concatUInt8Array,
    removePrefixIfNeeded,
)
from .message_padding import remove_message_padding
from .message_encrypt import (
    Envelope,
    EnvelopeType,
    Keypair,
)


@dataclass
class EnvelopePlus:
    """Envelope with some additional metadata."""

    id: str
    source: Optional[str]
    content: bytes
    receivedAt: int
    senderIdentity: Optional[str]
    timestamp: int
    type: EnvelopeType


def extract_content(message: str) -> Optional[bytes]:
    """
    Extract envelope bytes from a wrapped websocket message.

    Args:
        message (str): Base64 encoded websocket message.

    Returns:
        Optional[bytes]: Envelope bytes if present.
    """

    data_plaintext = base64ToUint8Array(message)
    try:
        ws_obj = json.loads(data_plaintext.decode())
        if ws_obj.get("type") == "REQUEST" and ws_obj.get("request"):
            body_b64 = ws_obj["request"].get("body")
            if body_b64:
                return base64.b64decode(body_b64)
        return None
    except Exception as exc:
        raise ValueError("Failed to extract websocket content") from exc


def _decode_envelope(data: bytes) -> Envelope:
    obj = json.loads(data.decode())
    content = base64.b64decode(obj["content"])
    return Envelope(
        type=EnvelopeType(obj["type"]),
        source=obj.get("source"),
        timestamp=int(obj["timestamp"]),
        content=content,
    )


def decode_message(
    body: bytes,
    *,
    override_source: Optional[str] = None,
    our_pub_key: Optional[str] = None,
) -> Optional[EnvelopePlus]:
    """
    Decode an envelope into an :class:`EnvelopePlus` structure.

    Args:
        override_source (Optional[str]): Override the source field.
        our_pub_key (Optional[str]): Our own public key for filtering.

    Returns:
        Optional[EnvelopePlus]: Parsed envelope or ``None``.
    """

    envelope = _decode_envelope(body)
    sender_identity = envelope.source
    source = envelope.source

    if override_source:
        sender_identity = envelope.source
        if sender_identity == our_pub_key:
            return None
        source = override_source

    return EnvelopePlus(
        id=str(uuid.uuid4()),
        source=source,
        content=envelope.content,
        receivedAt=int(time.time() * 1000),
        senderIdentity=sender_identity or source,
        timestamp=envelope.timestamp,
        type=envelope.type,
    )


def decrypt_message(keypairs: List[Keypair], envelope: EnvelopePlus) -> bytes:
    """
    Decrypt the content of an :class:`EnvelopePlus`.

    Args:
        keypairs (List[Keypair]): Available keypairs for decryption.
        envelope (EnvelopePlus): Envelope plus metadata.

    Returns:
        bytes: Decrypted and unpadded plaintext.
    """

    if not envelope.content:
        raise ValueError("Received an empty envelope")

    if envelope.type == EnvelopeType.SESSION_MESSAGE:
        return decrypt_envelope_with_our_key(keypairs[0], envelope)
    if envelope.type == EnvelopeType.CLOSED_GROUP_MESSAGE:
        return _decrypt_for_closed_group(list(keypairs), envelope)

    raise ValueError(f"Unknown message type: {envelope.type}")


def decrypt_envelope_with_our_key(keypair: Keypair, envelope: EnvelopePlus) -> bytes:
    """
    Decrypt an envelope addressed to us.

    Args:
        keypair (Keypair): Our keypair.
        envelope (EnvelopePlus): Envelope to decrypt.

    Returns:
        bytes: Decrypted plaintext without padding.
    """

    plaintext = decrypt_with_session_protocol(keypair, envelope)
    return remove_message_padding(plaintext)


def _decrypt_for_closed_group(keypairs: List[Keypair], envelope: EnvelopePlus) -> bytes:
    for _ in range(len(keypairs)):
        kp = keypairs.pop()
        try:
            decrypted = decrypt_with_session_protocol(kp, envelope, is_closed_group=True)
            if decrypted:
                return remove_message_padding(decrypted)
        except Exception:
            pass
    raise ValueError("Could not decrypt message for closed group")


def decrypt_with_session_protocol(
    keypair: Keypair,
    envelope: EnvelopePlus,
    *,
    is_closed_group: bool = False,
) -> bytes:
    """
    Low level decryption using the Session protocol.

    Args:
        keypair (Keypair): Keypair for decryption.
        envelope (EnvelopePlus): Envelope to decrypt.
        is_closed_group (bool): Whether this is a closed group message.

    Returns:
        bytes: Decrypted plaintext.
    """

    recipient_pub = removePrefixIfNeeded(keypair.x25519.publicKey)

    plaintext_with_meta = bindings.crypto_box_seal_open(
        envelope.content,
        recipient_pub,
        keypair.x25519.privateKey,
    )
    sig_size = bindings.crypto_sign_BYTES
    pk_size = bindings.crypto_sign_PUBLICKEYBYTES
    if len(plaintext_with_meta) <= sig_size + pk_size:
        raise ValueError("Decryption failed")

    signature = plaintext_with_meta[-sig_size:]
    sender_ed_pub = plaintext_with_meta[-(sig_size + pk_size) : -sig_size]
    plaintext = plaintext_with_meta[: -(sig_size + pk_size)]

    verification_data = concatUInt8Array(plaintext, sender_ed_pub, recipient_pub)
    try:
        signing.VerifyKey(sender_ed_pub).verify(verification_data, signature)
    except Exception as exc:
        raise ValueError("Invalid message signature") from exc

    sender_x_pub = bindings.crypto_sign_ed25519_pk_to_curve25519(sender_ed_pub)
    if sender_x_pub is None:
        raise ValueError("Failed to get sender public key")

    identity_hex = Uint8ArrayToHex(sender_x_pub)
    if is_closed_group:
        envelope.senderIdentity = identity_hex
    else:
        envelope.source = identity_hex

    return plaintext
