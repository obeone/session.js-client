import asyncio
from nacl import bindings, signing, hash
from nacl.encoding import RawEncoder

from session_py_client import Session
from session_py_client.sogs import blind_session_id, sign_sogs_request
from session_py_client.utils import hexToUint8Array
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
