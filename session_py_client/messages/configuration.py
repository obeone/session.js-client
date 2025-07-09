from dataclasses import dataclass
from typing import List

from ..utils import SessionValidationError, SessionValidationErrorCode
from ..protobuf import signalservice_pb2
from .base import ContentMessage
from ..utils import hexToUint8Array


@dataclass
class ConfigurationMessageContact:
    '''Contact entry for ConfigurationMessage.'''

    public_key: bytes
    display_name: str
    profile_picture_url: str | None = None
    profile_key: bytes | None = None
    is_approved: bool | None = None
    is_blocked: bool | None = None
    did_approve_me: bool | None = None

    def to_proto(self) -> signalservice_pb2.ConfigurationMessage.Contact:
        proto = signalservice_pb2.ConfigurationMessage.Contact()
        proto.publicKey = self.public_key
        proto.name = self.display_name
        if self.profile_picture_url is not None:
            proto.profilePicture = self.profile_picture_url
        if self.profile_key is not None:
            proto.profileKey = self.profile_key
        if self.is_approved is not None:
            proto.isApproved = self.is_approved
        if self.is_blocked is not None:
            proto.isBlocked = self.is_blocked
        if self.did_approve_me is not None:
            proto.didApproveMe = self.did_approve_me
        return proto


@dataclass
class ConfigurationMessageClosedGroup:
    '''Closed group definition for ConfigurationMessage.'''

    public_key: bytes
    name: str
    encryption_key_pair: dict
    members: List[str]
    admins: List[str]

    def to_proto(self) -> signalservice_pb2.ConfigurationMessage.ClosedGroup:
        proto = signalservice_pb2.ConfigurationMessage.ClosedGroup()
        proto.publicKey = self.public_key
        proto.name = self.name
        proto.encryptionKeyPair.publicKey = self.encryption_key_pair["publicKeyData"]
        proto.encryptionKeyPair.privateKey = self.encryption_key_pair["privateKeyData"]
        proto.members.extend(hexToUint8Array(m) for m in self.members)
        proto.admins.extend(hexToUint8Array(a) for a in self.admins)
        return proto

@dataclass
class ConfigurationMessage(ContentMessage):
    '''
    Legacy configuration message.

    Args:
        active_closed_groups (List[ConfigurationMessageClosedGroup]): Closed groups.
        active_open_groups (List[str]): List of open group URLs.
        display_name (str): Display name.
        profile_picture (str | None): URL of profile picture.
        profile_key (bytes | None): Profile encryption key.
        contacts (List[ConfigurationMessageContact]): Contact list.
    '''

    active_closed_groups: List[ConfigurationMessageClosedGroup] = None
    active_open_groups: List[str] = None
    display_name: str = ""
    profile_picture: str | None = None
    profile_key: bytes | None = None
    contacts: List[ConfigurationMessageContact] | None = None

    def __post_init__(self) -> None:
        if not self.active_closed_groups:
            raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, 'closed group must be set')
        if not self.active_open_groups:
            raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, 'open group must be set')
        if not self.display_name:
            raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, 'displayName must be set')
        if self.contacts is None:
            raise SessionValidationError(SessionValidationErrorCode.INVALID_OPTIONS, 'contacts must be set')

    def content_proto(self) -> signalservice_pb2.Content:
        content = signalservice_pb2.Content()
        content.configurationMessage.CopyFrom(self.configuration_proto())
        return content

    def configuration_proto(self) -> signalservice_pb2.ConfigurationMessage:
        proto = signalservice_pb2.ConfigurationMessage()
        proto.closedGroups.extend(cg.to_proto() for cg in self.active_closed_groups)
        proto.openGroups.extend(self.active_open_groups)
        proto.displayName = self.display_name
        if self.profile_picture is not None:
            proto.profilePicture = self.profile_picture
        if self.profile_key is not None:
            proto.profileKey = self.profile_key
        proto.contacts.extend(c.to_proto() for c in self.contacts)
        return proto
