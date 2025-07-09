from dataclasses import dataclass
from typing import Optional

from ..profile import Profile, serialize_profile
from ..protobuf import signalservice_pb2
from .base import ContentMessage


@dataclass
class MessageRequestResponse(ContentMessage):
    '''
    Response to a conversation request.

    Args:
        profile (Optional[Profile]): Sender profile information.
    '''

    profile: Optional[Profile] = None

    def __post_init__(self) -> None:
        if self.profile is not None:
            serialized = serialize_profile(self.profile)
            self._profile = serialized.get("lokiProfile")
            self._profile_key = serialized.get("profileKey")
        else:
            self._profile = None
            self._profile_key = None

    def content_proto(self) -> signalservice_pb2.Content:
        content = signalservice_pb2.Content()
        content.messageRequestResponse.CopyFrom(self.message_request_response_proto())
        return content

    def message_request_response_proto(self) -> signalservice_pb2.MessageRequestResponse:
        msg = signalservice_pb2.MessageRequestResponse()
        msg.isApproved = True
        if self._profile_key:
            msg.profileKey = self._profile_key
        if self._profile:
            prof = signalservice_pb2.DataMessage.LokiProfile()
            if "displayName" in self._profile:
                prof.displayName = self._profile["displayName"]
            if "profilePicture" in self._profile:
                prof.profilePicture = self._profile["profilePicture"]
            msg.profile.CopyFrom(prof)
        return msg
