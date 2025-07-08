from dataclasses import dataclass
from typing import List

from ..protobuf import signalservice_pb2
from .base import ContentMessage


@dataclass
class ReceiptMessage(ContentMessage):
    '''Base class for receipt messages.'''

    timestamps: List[int]

    def get_receipt_type(self) -> signalservice_pb2.ReceiptMessage.Type:
        '''Return the receipt type.'''
        raise NotImplementedError

    def content_proto(self) -> signalservice_pb2.Content:
        content = signalservice_pb2.Content()
        content.receiptMessage.CopyFrom(self.receipt_proto())
        return content

    def receipt_proto(self) -> signalservice_pb2.ReceiptMessage:
        proto = signalservice_pb2.ReceiptMessage()
        proto.type = self.get_receipt_type()
        proto.timestamp.extend(self.timestamps)
        return proto


@dataclass
class ReadReceiptMessage(ReceiptMessage):
    '''Receipt indicating that a message was read.'''

    def get_receipt_type(self) -> signalservice_pb2.ReceiptMessage.Type:
        return signalservice_pb2.ReceiptMessage.READ
