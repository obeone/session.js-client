# -*- coding: utf-8 -*-

"""
Tests for the Signal message schema.
"""

import pytest
from session_py.messages.schema.signal import Signal, Content, DataMessage, encode, decode

@pytest.mark.parametrize("envelope_type", list(Signal.Type))
def test_signal_roundtrip(envelope_type):
    """
    Tests that a Signal envelope can be encoded and decoded successfully,
    preserving all its attributes.
    """
    # 1. Create a Signal envelope instance with test data
    original_content = Content(dataMessage=DataMessage(body="test message", timestamp=12345))
    original_envelope = Signal(
        type=envelope_type,
        content=original_content.encode(),
        timestamp=67890,
        source="test-source"
    )

    # 2. Encode the envelope
    encoded_envelope = encode(original_envelope)

    # 3. Decode the envelope
    decoded_envelope = decode(encoded_envelope)

    # 4. Assert that the decoded envelope is identical to the original
    assert decoded_envelope.type == original_envelope.type
    assert decoded_envelope.timestamp == original_envelope.timestamp
    assert decoded_envelope.source == original_envelope.source
    
    # 5. Decode the inner content and assert its equality
    decoded_content = Content.decode(decoded_envelope.content)
    assert decoded_content == original_content

def test_decode_invalid_type():
    """
    Tests that decoding an envelope with an invalid type raises a ValueError.
    """
    # Create a dummy envelope with an invalid type value (e.g., 99)
    invalid_envelope_dict = {
        'type': 99,
        'content': b'some content',
        'timestamp': 12345,
        'source': 'some-source'
    }
    import msgpack
    encoded_invalid_envelope = msgpack.packb(invalid_envelope_dict)

    with pytest.raises(ValueError, match="Decoded envelope has an unknown type: 99"):
        decode(encoded_invalid_envelope)
