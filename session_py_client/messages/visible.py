from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..profile import Profile, serialize_profile
from ..protobuf import signalservice_pb2
from .base import ExpirableMessage


@dataclass
class AttachmentPointer:
    '''
    Description of an attachment stored on the file server.

    Args:
        id (int): Attachment identifier.
        url (str): Attachment download URL.
    '''

    id: int
    url: str
    content_type: Optional[str] = None
    key: Optional[bytes] = None
    size: Optional[int] = None
    digest: Optional[bytes] = None
    file_name: Optional[str] = None
    flags: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    caption: Optional[str] = None

    def to_proto(self) -> signalservice_pb2.AttachmentPointer:
        '''Return protobuf representation of the attachment pointer.'''
        msg = signalservice_pb2.AttachmentPointer()
        msg.id = self.id
        msg.url = self.url
        if self.content_type is not None:
            msg.contentType = self.content_type
        if self.key is not None:
            msg.key = self.key
        if self.size is not None:
            msg.size = self.size
        if self.digest is not None:
            msg.digest = self.digest
        if self.file_name is not None:
            msg.fileName = self.file_name
        if self.flags is not None:
            msg.flags = self.flags
        if self.width is not None:
            msg.width = self.width
        if self.height is not None:
            msg.height = self.height
        if self.caption is not None:
            msg.caption = self.caption
        return msg


@dataclass
class QuotedAttachment:
    '''Attachment reference inside a quoted message.'''

    content_type: Optional[str] = None
    file_name: Optional[str] = None
    thumbnail: Optional[AttachmentPointer] = None

    def to_proto(self) -> signalservice_pb2.DataMessage.Quote.QuotedAttachment:
        '''Return protobuf representation of quoted attachment.'''
        qa = signalservice_pb2.DataMessage.Quote.QuotedAttachment()
        if self.content_type is not None:
            qa.contentType = self.content_type
        if self.file_name is not None:
            qa.fileName = self.file_name
        if self.thumbnail is not None:
            qa.thumbnail.CopyFrom(self.thumbnail.to_proto())
        return qa


@dataclass
class Quote:
    '''
    Quoted message included with the visible message.

    Args:
        id (int): Original message timestamp.
        author (str): Author of the original message.
    '''

    id: int
    author: str
    text: Optional[str] = None
    attachments: Optional[List[QuotedAttachment]] = None

    def to_proto(self) -> signalservice_pb2.DataMessage.Quote:
        '''Return protobuf representation of the quote.'''
        q = signalservice_pb2.DataMessage.Quote()
        q.id = self.id
        q.author = self.author
        if self.text is not None:
            q.text = self.text
        if self.attachments:
            q.attachments.extend(att.to_proto() for att in self.attachments)
        return q


@dataclass
class Preview:
    '''Preview of a link included in the message.'''

    url: str
    title: Optional[str] = None
    image: Optional[AttachmentPointer] = None

    def to_proto(self) -> signalservice_pb2.DataMessage.Preview:
        '''Return protobuf representation of the preview.'''
        p = signalservice_pb2.DataMessage.Preview()
        p.url = self.url
        if self.title is not None:
            p.title = self.title
        if self.image is not None:
            p.image.CopyFrom(self.image.to_proto())
        return p


@dataclass
class Reaction:
    '''Representation of a message reaction.'''

    id: int
    author: str
    emoji: str
    action: signalservice_pb2.DataMessage.Reaction.Action

    def to_proto(self) -> signalservice_pb2.DataMessage.Reaction:
        '''Return protobuf representation of the reaction.'''
        r = signalservice_pb2.DataMessage.Reaction()
        r.id = self.id
        r.author = self.author
        r.emoji = self.emoji
        r.action = self.action
        return r


@dataclass
class VisibleMessage(ExpirableMessage):
    '''
    Standard user message containing text and attachments.

    Args:
        attachments (Optional[List[AttachmentPointer]]): List of attachments.
        body (Optional[str]): Optional text body.
        quote (Optional[Quote]): Quoted message details.
        profile (Optional[Profile]): Sender profile information.
        preview (Optional[List[Preview]]): Link previews.
        reaction (Optional[Reaction]): Reaction synchronisation.
        sync_target (Optional[str]): Target conversation for synced messages.
    '''

    attachments: Optional[List[AttachmentPointer]] = None
    body: Optional[str] = None
    quote: Optional[Quote] = None
    profile: Optional[Profile] = None
    preview: Optional[List[Preview]] = None
    reaction: Optional[Reaction] = None
    sync_target: Optional[str] = None

    def content_proto(self) -> signalservice_pb2.Content:
        content = super().content_proto()
        content.dataMessage.CopyFrom(self.data_proto())
        return content

    def data_proto(self) -> signalservice_pb2.DataMessage:
        data = super().data_proto()
        if self.body is not None:
            data.body = self.body
        if self.attachments:
            data.attachments.extend(att.to_proto() for att in self.attachments)
        if self.preview:
            data.preview.extend(p.to_proto() for p in self.preview)
        if self.reaction is not None:
            data.reaction.CopyFrom(self.reaction.to_proto())
        if self.sync_target is not None:
            data.syncTarget = self.sync_target
        if self.profile is not None:
            serialized = serialize_profile(self.profile)
            loki_profile = serialized.get("lokiProfile")
            if loki_profile:
                prof = signalservice_pb2.DataMessage.LokiProfile()
                if "displayName" in loki_profile:
                    prof.displayName = loki_profile["displayName"]
                if "profilePicture" in loki_profile:
                    prof.profilePicture = loki_profile["profilePicture"]
                data.profile.CopyFrom(prof)
            if serialized.get("profileKey"):
                data.profileKey = serialized["profileKey"]
        if self.quote is not None:
            data.quote.CopyFrom(self.quote.to_proto())
        data.timestamp = self.timestamp
        return data
