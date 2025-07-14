# -*- coding: utf-8 -*-

import pytest
import secrets
import nacl.bindings
from nacl.signing import SigningKey
from session_py.crypto.keypair import Keypair, SigningKeypair, BoxKeypair
from session_py.crypto.message_encrypt import encrypt
from session_py.crypto.message_decrypt import decrypt
from session_py.messages.schema.signal import Signal as Envelope

def generate_full_keypair():
    """Generates a full Ed25519 and X25519 keypair."""
    ed25519_priv = SigningKey.generate()
    ed25519_pub = ed25519_priv.verify_key

    # Convert Ed25519 keys to Curve25519 keys for encryption
    x25519_priv = ed25519_priv.to_curve25519_private_key()
    x25519_pub = x25519_priv.public_key

    return Keypair(
        ed25519=SigningKeypair(pub_key=bytes(ed25519_pub), priv_key=bytes(ed25519_priv)),
        x25519=BoxKeypair(pub_key=bytes(x25519_pub), priv_key=bytes(x25519_priv))
    )

@pytest.fixture
def sender_keypair():
    """Provides a random Keypair for the sender."""
    return generate_full_keypair()

@pytest.fixture
def recipient_keypair():
    """Provides a random Keypair for the recipient."""
    return generate_full_keypair()

@pytest.fixture
def group_id():
    """Provides a random 32-byte hex string to be used as a group key."""
    return secrets.token_hex(32)

@pytest.fixture
def test_message():
    """Provides a sample message for testing."""
    return b"This is a test message for encryption and decryption."

@pytest.mark.asyncio
async def test_session_message_encryption_decryption(sender_keypair, recipient_keypair, test_message):
    """
    Tests the full encryption and decryption flow for a SESSION_MESSAGE.
    It encrypts a message from a sender to a recipient and then decrypts it,
    verifying that the original message is recovered.
    """
    # 1. Encrypt the message for a 1-to-1 session
    encrypted_result = await encrypt(
        sender_keypair=sender_keypair,
        recipient=recipient_keypair.x25519.pub_key.hex(),
        plain_text_buffer=test_message,
        encryption_type=Envelope.Type.SESSION_MESSAGE
    )

    assert encrypted_result.envelope_type == Envelope.Type.SESSION_MESSAGE

    # 2. Decrypt the message
    decrypted_message = decrypt(
        recipient_keypair=recipient_keypair,
        ciphertext=encrypted_result.cipher_text,
        envelope_type=encrypted_result.envelope_type,
        sender_x25519_pubkey_hex=sender_keypair.x25519.pub_key.hex()
    )

    # 3. Verify the decrypted message matches the original
    assert decrypted_message == test_message

@pytest.mark.asyncio
async def test_group_message_encryption_decryption(sender_keypair, recipient_keypair, group_id, test_message):
    """
    Tests the full encryption and decryption flow for a CLOSED_GROUP_MESSAGE.
    It encrypts a message for a group and then decrypts it using the shared group key,
    verifying that the original message is recovered.
    """
    # 1. Encrypt the message for the group
    encrypted_result = await encrypt(
        sender_keypair=sender_keypair,
        recipient=group_id,
        plain_text_buffer=test_message,
        encryption_type=Envelope.Type.CLOSED_GROUP_MESSAGE
    )

    assert encrypted_result.envelope_type == Envelope.Type.CLOSED_GROUP_MESSAGE

    # 2. Decrypt the message using the group secret
    # The recipient_keypair is not used for group decryption but is required by the function signature.
    decrypted_message = decrypt(
        recipient_keypair=recipient_keypair,
        ciphertext=encrypted_result.cipher_text,
        envelope_type=encrypted_result.envelope_type,
        group_id=group_id
    )

    # 3. Verify the decrypted message matches the original
    assert decrypted_message == test_message
