from dataclasses import dataclass

from ..protobuf import signalservice_pb2
from .base import ContentMessage


@dataclass
class SharedConfigMessage(ContentMessage):
    '''
    Message used to synchronise application configuration.

    Args:
        seqno (int): Sequence number.
        kind (signalservice_pb2.SharedConfigMessage.Kind): Config kind.
        data (bytes): Serialized configuration data.
    '''

    seqno: int = 0
    kind: signalservice_pb2.SharedConfigMessage.Kind = (
        signalservice_pb2.SharedConfigMessage.USER_PROFILE
    )
    data: bytes = b""

    def content_proto(self) -> signalservice_pb2.Content:
        content = signalservice_pb2.Content()
        content.sharedConfigMessage.CopyFrom(self.shared_config_proto())
        return content

    def ttl(self) -> int:
        # 30 days
        return 30 * 24 * 60 * 60 * 1000

    def shared_config_proto(self) -> signalservice_pb2.SharedConfigMessage:
        msg = signalservice_pb2.SharedConfigMessage()
        msg.data = self.data
        msg.kind = self.kind
        msg.seqno = self.seqno
        return msg
