from dataclasses import dataclass

from ..protobuf import signalservice_pb2
from .base import ContentMessage


@dataclass
class UnsendMessage(ContentMessage):
    '''
    Message used to delete a previously sent message.

    Args:
        author (str): Sender of the unsend message.
    '''

    author: str = ""

    def content_proto(self) -> signalservice_pb2.Content:
        content = signalservice_pb2.Content()
        content.unsendMessage.CopyFrom(self.unsend_proto())
        return content

    def unsend_proto(self) -> signalservice_pb2.Unsend:
        msg = signalservice_pb2.Unsend()
        msg.timestamp = self.timestamp
        msg.author = self.author
        return msg
