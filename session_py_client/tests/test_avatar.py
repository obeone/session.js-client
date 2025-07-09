import asyncio
import os

from session_py_client.profile import (
    upload_avatar,
    download_avatar,
    Avatar,
    PROFILE_KEY_LENGTH,
)
from session_py_client import Session


class DummyNetwork:
    def __init__(self):
        self.requests = []

    async def on_request(self, type_, body):
        self.requests.append((type_, body))
        if type_ == "UploadAttachment":
            return {"url": "http://filev2.getsession.org/file/42"}
        if type_ == "DownloadAttachment":
            return b"encrypted"
        return None


def test_upload_avatar(monkeypatch):
    network = DummyNetwork()
    session = Session(network=network)

    monkeypatch.setattr(
        "session_py_client.profile.encrypt_profile", lambda data, key: b"enc" + data
    )
    monkeypatch.setattr(os, "urandom", lambda n: b"\x01" * n)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(upload_avatar(session, b"img"))
    loop.close()
    asyncio.set_event_loop(None)

    assert result["avatarPointer"].endswith("42")
    assert result["profileKey"] == b"\x01" * PROFILE_KEY_LENGTH
    req_type, body = network.requests[0]
    assert req_type == "UploadAttachment"
    assert body["data"] == b"enc" + b"img"

def test_download_avatar(monkeypatch):
    network = DummyNetwork()
    session = Session(network=network)
    avatar = Avatar(url="http://filev2.getsession.org/file/42", key=b"k" * PROFILE_KEY_LENGTH)

    monkeypatch.setattr(
        "session_py_client.profile.decrypt_profile", lambda data, key: b"dec"
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(download_avatar(session, avatar))
    loop.close()
    asyncio.set_event_loop(None)

    assert result == b"dec"
    req_type, body = network.requests[0]
    assert req_type == "DownloadAttachment"
    assert body["id"] == "42"
