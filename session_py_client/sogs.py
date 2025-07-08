from __future__ import annotations

"""SOGS utilities compatible with Session.py."""

import base64
import time
from typing import Any, Optional

from nacl import bindings, utils

from .crypto import add_message_padding, Keypair
from .utils import (
    Uint8ArrayToBase64,
    hexToUint8Array,
    SessionValidationError,
    SessionValidationErrorCode,
)
from network import (
    sign_sogs_request as _sign_sogs_request,
    _get_blinding_values,
    _blinded_ed25519_signature,
)


async def blind_session_id(self: Any, server_pk: str) -> str:
    """Return blinded Session ID using server public key."""

    if getattr(self, "session_id", None) is None or getattr(self, "keypair", None) is None:
        raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Instance is not initialized")
    blinding = _get_blinding_values(hexToUint8Array(server_pk), self.keypair.ed25519)
    return "15" + blinding["publicKey"].hex()


def encode_sogs_message(
    self: Any,
    *,
    server_pk: str,
    message: Any,
    blind: bool,
) -> dict[str, str]:
    """Encode a message for SOGS storage and return data and signature."""

    if getattr(self, "session_id", None) is None or getattr(self, "keypair", None) is None:
        raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Instance is not initialized")

    padded = add_message_padding(message.plain_text_buffer())
    data = Uint8ArrayToBase64(padded)

    if blind:
        blinding = _get_blinding_values(hexToUint8Array(server_pk), self.keypair.ed25519)
        sig_bytes = _blinded_ed25519_signature(
            padded,
            self.keypair,
            blinding["secretKey"],
            blinding["publicKey"],
        )
        signature = Uint8ArrayToBase64(sig_bytes)
    else:
        sig_bytes = bindings.crypto_sign_detached(padded, self.keypair.ed25519.privateKey)
        signature = Uint8ArrayToBase64(sig_bytes)

    return {"data": data, "signature": signature}


def sign_sogs_request(
    self: Any,
    *,
    blind: bool,
    server_pk: str,
    timestamp: int,
    endpoint: str,
    nonce: bytes,
    method: str,
    body: Optional[bytes] = None,
) -> bytes:
    """Sign a SOGS request."""

    if getattr(self, "session_id", None) is None or getattr(self, "keypair", None) is None:
        raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Instance is not initialized")
    return _sign_sogs_request(
        blind=blind,
        server_pk=server_pk,
        timestamp=timestamp,
        endpoint=endpoint,
        nonce=nonce,
        method=method,
        keypair=self.keypair,
        body=body,
    )


async def send_sogs_request(
    self: Any,
    *,
    host: str,
    server_pk: str,
    endpoint: str,
    method: str,
    body: Optional[Any] = None,
    blind: bool = True,
) -> Any:
    """Encrypt, sign and send a request to a SOGS server."""

    if getattr(self, "session_id", None) is None or getattr(self, "keypair", None) is None:
        raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Instance is not initialized")
    if getattr(self, "network", None) is None:
        raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, "Network not configured")

    nonce = utils.random(16)
    timestamp = int(time.time())

    body_bytes = None
    if isinstance(body, str):
        body_bytes = body.encode()
    elif isinstance(body, (bytes, bytearray)):
        body_bytes = bytes(body)

    signature = sign_sogs_request(
        self,
        blind=blind,
        server_pk=server_pk,
        timestamp=timestamp,
        endpoint=endpoint,
        nonce=nonce,
        method=method,
        body=body_bytes,
    )

    if blind:
        pubkey = await blind_session_id(self, server_pk)
    else:
        pubkey = "00" + self.keypair.ed25519.publicKey.hex()

    content_type = None
    processed_body = None
    if body is not None:
        if isinstance(body, (bytes, bytearray)):
            content_type = "application/octet-stream"
            processed_body = bytes(body)
        else:
            content_type = "application/json"
            processed_body = body

    headers = {
        "X-SOGS-Pubkey": pubkey,
        "X-SOGS-Timestamp": str(timestamp),
        "X-SOGS-Nonce": base64.b64encode(nonce).decode("ascii"),
        "X-SOGS-Signature": base64.b64encode(signature).decode("ascii"),
    }
    if content_type:
        headers["Content-Type"] = content_type

    request_body = {
        "host": host,
        "endpoint": endpoint,
        "method": method,
        "body": processed_body,
        "headers": headers,
    }

    return await self.network.on_request("sogs_request", request_body)
