from dataclasses import dataclass
from typing import Optional

from ..protobuf import signalservice_pb2
from .base import ContentMessage


@dataclass
class TypingMessage(ContentMessage):
    '''
    Message representing typing indicator state.

    Args:
        is_typing (bool): ``True`` if typing indicator started.
        typing_timestamp (Optional[int]): Timestamp associated with the event.
    '''

    is_typing: bool
    typing_timestamp: Optional[int] = None

    def ttl(self) -> int:
        return 20 * 1000

    def content_proto(self) -> signalservice_pb2.Content:
        content = signalservice_pb2.Content()
        content.typingMessage.CopyFrom(self.typing_proto())
        return content

    def typing_proto(self) -> signalservice_pb2.TypingMessage:
        action = (signalservice_pb2.TypingMessage.STARTED
                  if self.is_typing else signalservice_pb2.TypingMessage.STOPPED)
        msg = signalservice_pb2.TypingMessage()
        msg.action = action
        msg.timestamp = self.typing_timestamp or 0
        return msg
