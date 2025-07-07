import base64

from session_py_client.crypto import (
    generate_keypair,
    encrypt,
    decrypt_envelope_with_our_key,
    build_envelope,
    wrap_envelope,
    extract_content,
    decode_message,
    EnvelopeType,
    add_message_padding,
    remove_message_padding,
)


def test_message_padding_roundtrip():
    msg = b"test"
    padded = add_message_padding(msg)
    assert padded != msg
    plain = remove_message_padding(padded)
    assert plain == msg


def test_encrypt_decrypt_roundtrip():
    sender = generate_keypair()
    recipient = generate_keypair()

    plaintext = b"hello world"
    enc = encrypt(sender, base64.b16encode(recipient.x25519.publicKey).decode("ascii"), plaintext, EnvelopeType.SESSION_MESSAGE)
    env = build_envelope(EnvelopeType.SESSION_MESSAGE, None, 12345, enc.cipherText)
    wrapped = wrap_envelope(env)
    data64 = base64.b64encode(wrapped).decode("ascii")

    body = extract_content(data64)
    assert body is not None
    env_plus = decode_message(body)
    assert env_plus is not None

    decrypted = decrypt_envelope_with_our_key(recipient, env_plus)
    assert decrypted == plaintext
