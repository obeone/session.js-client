# -*- coding: utf-8 -*-

"""
This module defines the data structures for Session messages, based on the Signal protocol.
"""

import msgpack
from typing import Optional
from enum import IntEnum


class DataMessage:
    """
    Represents a data message within the Signal protocol.
    """
    def __init__(self, body: str, timestamp: int, author_session_id: Optional[str] = None, **kwargs):
        self.body = body
        self.timestamp = timestamp
        self.author_session_id = author_session_id
        # Catch any other fields that might be present
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __eq__(self, other):
        if not isinstance(other, DataMessage):
            return NotImplemented
        return self.__dict__ == other.__dict__


class Content:
    """
    Represents the content of a message, which can be one of several types.
    """
    def __init__(self, dataMessage: Optional[DataMessage] = None, **kwargs):
        self.dataMessage = dataMessage
        # Catch any other fields that might be present
        for key, value in kwargs.items():
            setattr(self, key, value)

    def encode(self) -> bytes:
        """
        Encodes the content object to bytes using msgpack.

        Serializes the Content object, including the DataMessage if present,
        and any additional attributes, into a msgpack byte string.

        :return: The msgpack-encoded byte string.
        """
        # Build a dictionary with non-None values
        data = {}
        if self.dataMessage:
            dm_data = {
                'body': self.dataMessage.body,
                'timestamp': self.dataMessage.timestamp,
                'author_session_id': self.dataMessage.author_session_id
            }
            # Add any extra attributes from DataMessage
            for key, value in self.dataMessage.__dict__.items():
                if key not in ['body', 'timestamp', 'author_session_id']:
                    dm_data[key] = value
            data['dataMessage'] = dm_data

        # Add any extra attributes from Content
        for key, value in self.__dict__.items():
            if key not in ['dataMessage']:
                data[key] = value

        return msgpack.packb(data, use_bin_type=True) or b''

    @classmethod
    def decode(cls, buffer: bytes) -> 'Content':
        """
        Decodes bytes to a Content object using msgpack.

        Deserializes a msgpack byte string into a Content object,
        reconstructing the DataMessage if present and including any
        additional attributes found in the data.

        :param buffer: The msgpack-encoded byte string.
        :return: The reconstructed Content object.
        """
        unpacked = msgpack.unpackb(buffer, raw=False)
        dm_data = unpacked.pop('dataMessage', None)

        data_message = DataMessage(**dm_data) if dm_data else None

        return cls(dataMessage=data_message, **unpacked)

    def __eq__(self, other):
        if not isinstance(other, Content):
            return NotImplemented
        return self.__dict__ == other.__dict__


class Signal:
    """
    Represents a message envelope that wraps the actual message content.
    """
    class Type(IntEnum):
        SESSION_MESSAGE = 1
        CLOSED_GROUP_MESSAGE = 3
        SYNC_MESSAGE = 4
        CALL_MESSAGE = 5
        RECEIPT_MESSAGE = 6
        VERIFICATION_MESSAGE = 7

    def __init__(self, type: Type, content: bytes, timestamp: int, source: Optional[str] = None, **kwargs):
        self.type = type
        self.content = content
        self.timestamp = timestamp
        self.source = source
        # Catch any other fields that might be present
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __eq__(self, other):
        if not isinstance(other, Signal):
            return NotImplemented
        return self.__dict__ == other.__dict__


def encode(envelope: Signal) -> bytes:
    """
    Encodes a Signal envelope object into bytes using msgpack.
    This implementation serializes the entire envelope object, including metadata
    like timestamp and source, which is an improvement over legacy formats
    that might only handle content.

    Args:
        envelope (Signal): The Signal envelope object to encode.

    Returns:
        bytes: The msgpack-encoded representation of the envelope.
    """
    # The envelope type is an IntEnum, so we need to convert it to its integer value for serialization.
    # We also gather all other attributes of the envelope.
    data_to_pack = envelope.__dict__.copy()
    data_to_pack['type'] = envelope.type.value
    return msgpack.packb(data_to_pack, use_bin_type=True) or b''


def decode(raw: bytes) -> Signal:
    """
    Decodes a msgpack-encoded byte string into a Signal envelope object.
    This function reconstructs the Signal object from its serialized form,
    restoring the envelope type and all other attributes.

    Args:
        raw (bytes): The msgpack-encoded byte string.

    Returns:
        Signal: The reconstructed Signal envelope object.

    Raises:
        ValueError: If the decoded type is not a valid Signal.Type.
    """
    unpacked = msgpack.unpackb(raw, raw=False)

    # Convert the integer type back to a Signal.Type enum member.
    try:
        unpacked['type'] = Signal.Type(unpacked['type'])
    except ValueError as e:
        raise ValueError(f"Decoded envelope has an unknown type: {unpacked.get('type')}") from e

    return Signal(**unpacked)
