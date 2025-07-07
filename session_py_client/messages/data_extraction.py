from dataclasses import dataclass

from ..protobuf import signalservice_pb2
from .base import ExpirableMessage


@dataclass
class DataExtractionNotificationMessage(ExpirableMessage):
    '''
    Notification about screenshot or media save events.

    Args:
        action (signalservice_pb2.DataExtractionNotification.Type): Event type.
        timestamp (int): Event timestamp.
    '''

    action: signalservice_pb2.DataExtractionNotification.Type
    extraction_timestamp: int

    def content_proto(self) -> signalservice_pb2.Content:
        content = super().content_proto()
        content.dataExtractionNotification.CopyFrom(self.data_extraction_proto())
        return content

    def data_extraction_proto(self) -> signalservice_pb2.DataExtractionNotification:
        msg = signalservice_pb2.DataExtractionNotification()
        msg.type = self.action
        msg.timestamp = self.extraction_timestamp
        return msg
