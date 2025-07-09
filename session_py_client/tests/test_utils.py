import asyncio
import pytest

from session_py_client.utils import (
    Uint8ArrayToHex,
    hexToUint8Array,
    concatUInt8Array,
    removePrefixIfNeeded,
    isHex,
    Uint8ArrayToBase64,
    base64ToUint8Array,
    Deferred,
    checkStorage,
    checkNetwork,
    SessionValidationError,
    SessionValidationErrorCode,
    get_placeholder_display_name,
)


def test_hex_conversions():
    data = b"\x01\x02\xab"
    hex_str = Uint8ArrayToHex(data)
    assert hex_str == "0102ab"
    assert hexToUint8Array(hex_str) == data


def test_concat_and_prefix():
    res = concatUInt8Array(b"ab", b"cd")
    assert res == b"abcd"
    assert removePrefixIfNeeded(b"\x05\xff") == b"\xff"
    assert removePrefixIfNeeded("05ff") == "ff"
    assert removePrefixIfNeeded(b"ab") == b"ab"
    assert removePrefixIfNeeded("ab") == "ab"


def test_is_hex():
    assert isHex("deadbeef")
    assert not isHex("xyz")


def test_base64_conversions():
    data = b"hello"
    encoded = Uint8ArrayToBase64(data)
    assert base64ToUint8Array(encoded) == data


def test_deferred():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    d = Deferred[int]()

    loop.call_soon(d.resolve, 5)
    result = loop.run_until_complete(d.promise)
    loop.close()
    asyncio.set_event_loop(None)
    assert result == 5


def test_check_storage_network():
    class Storage:
        def get(self, key):
            return None

        def set(self, key, value):
            pass

        def delete(self, key):
            pass

        def has(self, key):
            return False

    class Network:
        async def on_request(self, type_, body):
            return None

    checkStorage(Storage())
    checkNetwork(Network())

    with pytest.raises(SessionValidationError) as exc:
        checkStorage(object())
    assert exc.value.code == SessionValidationErrorCode.INVALID_OPTIONS

    class BadNetwork:
        pass

    with pytest.raises(SessionValidationError):
        checkNetwork(BadNetwork())


def test_get_placeholder_display_name():
    assert get_placeholder_display_name("1234567890abcdef") == "(1234...cdef)"

