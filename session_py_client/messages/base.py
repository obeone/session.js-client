from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4

from ..protobuf import signalservice_pb2


@dataclass
class SignalMessage:
    '''
    Base message containing timestamp and identifier.

    Args:
        timestamp (int): Message timestamp in milliseconds.
        identifier (Optional[str]): Optional unique identifier.
    '''

    timestamp: int
    identifier: str = field(default_factory=lambda: uuid4().hex)


@dataclass
class ContentMessage(SignalMessage):
    '''
    Message with serialisable content.
    '''

    def content_proto(self) -> signalservice_pb2.Content:
        '''Return protobuf representation of the message content.'''
        raise NotImplementedError

    def plain_text_buffer(self) -> bytes:
        '''Return serialized protobuf content.'''
        return self.content_proto().SerializeToString()

    def ttl(self) -> int:
        '''Return message time-to-live in milliseconds.'''
        return 14 * 24 * 60 * 60 * 1000


@dataclass
class ExpirableMessage(ContentMessage):
    '''
    Content message with optional expiration behaviour.

    Args:
        expiration_type (Optional[signalservice_pb2.Content.ExpirationType]): Expiration type.
        expire_timer (Optional[int]): Expiration timer in seconds.
    '''

    expiration_type: Optional[signalservice_pb2.Content.ExpirationType] = None
    expire_timer: Optional[int] = None

    def content_proto(self) -> signalservice_pb2.Content:
        content = signalservice_pb2.Content()
        if self.expiration_type is not None:
            content.expirationType = self.expiration_type
        if self.expire_timer is not None and self.expire_timer > -1:
            content.expirationTimer = self.expire_timer
        return content

    def data_proto(self) -> signalservice_pb2.DataMessage:
        data = signalservice_pb2.DataMessage()
        if (self.expiration_type in (signalservice_pb2.Content.UNKNOWN, None) and
                self.expire_timer is not None and self.expire_timer > -1):
            data.expireTimer = self.expire_timer
        return data

    def ttl(self) -> int:
        if self.expiration_type == signalservice_pb2.Content.DELETE_AFTER_SEND:
            return (self.expire_timer or 0) * 1000
        return super().ttl()
