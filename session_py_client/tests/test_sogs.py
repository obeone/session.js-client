import asyncio
from nacl import signing, hash
from nacl.encoding import RawEncoder

from session_py_client import Session
from session_py_client.sogs import (
    blind_session_id,
    sign_sogs_request,
    encode_sogs_message,
    send_sogs_request,
)
import session_py_client.sogs as sogs
from session_py_client.utils import hexToUint8Array
from session_py_client.crypto import add_message_padding
import base64
from network import _get_blinding_values, _blinded_ed25519_signature


def setup_session():
    session = Session()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(session.set_mnemonic("seed words for tests"))
    loop.close()
    asyncio.set_event_loop(None)
    return session


def test_blind_session_id():
    session = setup_session()
    server_pk = "11" * 32
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    blinded = loop.run_until_complete(blind_session_id(session, server_pk))
    loop.close()
    asyncio.set_event_loop(None)
    assert blinded.startswith("15") and len(blinded) == 66


def test_sign_sogs_request_unblinded():
    session = setup_session()
    server_pk = "22" * 32
    nonce = b"\x00" * 16
    timestamp = 1700000000
    endpoint = "/test"
    method = "POST"
    body = b"{}"
    sig = sign_sogs_request(
        session,
        blind=False,
        server_pk=server_pk,
        timestamp=timestamp,
        endpoint=endpoint,
        nonce=nonce,
        method=method,
        body=body,
    )
    pk = hexToUint8Array(server_pk)
    to_sign = pk + nonce + str(timestamp).encode() + method.encode() + endpoint.encode()
    to_sign += hash.blake2b(body, digest_size=64, encoder=RawEncoder)
    signing.VerifyKey(session.keypair.ed25519.publicKey).verify(to_sign, sig)


def test_sign_sogs_request_blinded():
    session = setup_session()
    server_pk = "33" * 32
    nonce = b"\x01" * 16
    timestamp = 1700000001
    endpoint = "/path"
    method = "GET"
    sig = sign_sogs_request(
        session,
        blind=True,
        server_pk=server_pk,
        timestamp=timestamp,
        endpoint=endpoint,
        nonce=nonce,
        method=method,
    )
    pk_bytes = hexToUint8Array(server_pk)
    to_sign = pk_bytes + nonce + str(timestamp).encode() + method.encode() + endpoint.encode()
    blinding = _get_blinding_values(pk_bytes, session.keypair.ed25519)
    expected = _blinded_ed25519_signature(
        to_sign,
        session.keypair,
        blinding["secretKey"],
        blinding["publicKey"],
    )
    assert sig == expected


def test_encode_sogs_message(monkeypatch):
    session = setup_session()
    server_pk = "44" * 32

    class DummyMessage:
        def plain_text_buffer(self):
            return b"hello"

    monkeypatch.setattr(
        sogs.bindings,
        "crypto_sign_detached",
        lambda msg, sk: signing.SigningKey(sk).sign(msg).signature,
        raising=False,
    )

    result = encode_sogs_message(
        session,
        server_pk=server_pk,
        message=DummyMessage(),
        blind=False,
    )

    padded = add_message_padding(b"hello")
    assert base64.b64decode(result["data"]) == padded
    signing.VerifyKey(session.keypair.ed25519.publicKey).verify(
        padded,
        base64.b64decode(result["signature"]),
    )


def test_send_sogs_request(monkeypatch):
    session = setup_session()

    class DummyNetwork:
        def __init__(self):
            self.requests = []

        async def on_request(self, type_, body):
            self.requests.append((type_, body))
            return {"ok": True}

    session.network = DummyNetwork()

    monkeypatch.setattr(sogs, "sign_sogs_request", lambda *a, **k: b"sig")
    async def fake_blind(*a, **k):
        return "15" + "00" * 32

    monkeypatch.setattr(sogs, "blind_session_id", fake_blind)
    monkeypatch.setattr(sogs.utils, "random", lambda n: b"\x00" * n)
    monkeypatch.setattr(sogs.time, "time", lambda: 1700000002)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        send_sogs_request(
            session,
            host="https://sogs.example.com",
            server_pk="11" * 32,
            endpoint="/test",
            method="POST",
            body="{}",
            blind=True,
        )
    )
    loop.close()
    asyncio.set_event_loop(None)

    req_type, body = session.network.requests[0]
    assert req_type == "sogs_request"
    assert body["endpoint"] == "/test"
    assert body["method"] == "POST"
    assert body["body"] == "{}"
    headers = body["headers"]
    assert headers["X-SOGS-Pubkey"].startswith("15")
    assert headers["X-SOGS-Timestamp"] == "1700000002"
    assert headers["X-SOGS-Nonce"] == base64.b64encode(b"\x00" * 16).decode("ascii")
    assert headers["X-SOGS-Signature"] == base64.b64encode(b"sig").decode("ascii")
