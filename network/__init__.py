"""Async network utilities using aiohttp."""

from __future__ import annotations

import json
from typing import Any, Optional

import aiohttp
from nacl import bindings, hash, signing
from nacl.encoding import RawEncoder

from session_py_client.crypto import Keypair
from session_py_client.utils import hexToUint8Array, concatUInt8Array


def _sha512_multipart(parts: list[bytes]) -> bytes:
    """Return SHA512 hash of concatenated byte parts."""
    return bindings.crypto_hash_sha512(concatUInt8Array(*parts))


def _blinded_ed25519_signature(message: bytes, keypair: Keypair, ka: bytes, kA: bytes) -> bytes:
    """Generate a blinded ED25519 signature."""
    s_encode = keypair.ed25519.privateKey[:32]
    sha_full = bindings.crypto_hash_sha512(s_encode)
    hrh = sha_full[32:]
    r = bindings.crypto_core_ed25519_scalar_reduce(
        _sha512_multipart([hrh, kA, message])
    )
    sig_r = bindings.crypto_scalarmult_ed25519_base_noclamp(r)
    hram = bindings.crypto_core_ed25519_scalar_reduce(
        _sha512_multipart([sig_r, kA, message])
    )
    sig_s = bindings.crypto_core_ed25519_scalar_add(
        r,
        bindings.crypto_core_ed25519_scalar_mul(hram, ka),
    )
    return concatUInt8Array(sig_r, sig_s)


def _get_blinding_values(server_pk: bytes, signing_keys: Keypair.ed25519.__class__) -> dict[str, bytes]:
    """Return blinding values for blinded signature."""
    k = bindings.crypto_core_ed25519_scalar_reduce(
        hash.blake2b(server_pk, digest_size=64, encoder=RawEncoder)
    )
    full_sk = signing_keys.privateKey + signing_keys.publicKey
    a = bindings.crypto_sign_ed25519_sk_to_curve25519(full_sk)
    if len(a) > 32:
        a = a[:32]
    ka = bindings.crypto_core_ed25519_scalar_mul(k, a)
    kA = bindings.crypto_scalarmult_ed25519_base_noclamp(ka)
    return {"a": a, "secretKey": ka, "publicKey": kA}


def sign_sogs_request(
    *,
    blind: bool,
    server_pk: str,
    timestamp: int,
    endpoint: str,
    nonce: bytes,
    method: str,
    keypair: Keypair,
    body: Optional[bytes] = None,
) -> bytes:
    """Sign a SOGS request using Ed25519, optionally with blinding."""
    pk = hexToUint8Array(server_pk)
    to_sign = concatUInt8Array(
        pk,
        nonce,
        str(timestamp).encode(),
        method.encode(),
        endpoint.encode(),
    )
    if body is not None:
        body_hash = hash.blake2b(body, digest_size=64, encoder=RawEncoder)
        to_sign = concatUInt8Array(to_sign, body_hash)
    if blind:
        blinding = _get_blinding_values(pk, keypair.ed25519)
        signature = _blinded_ed25519_signature(
            to_sign, keypair, blinding["secretKey"], blinding["publicKey"]
        )
        return signature
    signer = signing.SigningKey(keypair.ed25519.privateKey)
    return signer.sign(to_sign).signature


class Network:
    """Simple aiohttp-based network layer."""

    def __init__(
        self,
        base_url: str,
        *,
        proxy: Optional[str] = None,
        websocket_url: Optional[str] = None,
        keypair: Optional[Keypair] = None,
        session_id: Optional[str] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.proxy = proxy
        self.websocket_url = websocket_url
        self.keypair = keypair
        self.session_id = session_id
        self._session = aiohttp.ClientSession()
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None

    async def connect_ws(self) -> None:
        """Establish websocket connection if URL configured."""
        if self.websocket_url and self._ws is None:
            self._ws = await self._session.ws_connect(
                self.websocket_url, proxy=self.proxy
            )

    async def close(self) -> None:
        """Close underlying HTTP session and websocket."""
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
        await self._session.close()

    async def on_request(self, type_: str, body: Any) -> Any:
        """Send a request using HTTP POST or WebSocket."""
        if type_ == "websocket":
            await self.connect_ws()
            assert self._ws is not None
            await self._ws.send_str(json.dumps(body))
            msg = await self._ws.receive()
            return msg.data
        url = f"{self.base_url}/{type_}"
        async with self._session.post(url, json=body, proxy=self.proxy) as resp:
            resp.raise_for_status()
            ct = resp.headers.get("Content-Type", "")
            if ct.startswith("application/json"):
                return await resp.json()
            return await resp.read()
