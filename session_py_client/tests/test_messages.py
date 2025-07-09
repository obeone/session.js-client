from session_py_client.messages import (
    TypingMessage,
    DataExtractionNotificationMessage,
    SharedConfigMessage,
    MessageRequestResponse,
    UnsendMessage,
)
from session_py_client.profile import Profile, Avatar
from session_py_client.protobuf import signalservice_pb2


def test_typing_message_proto():
    msg = TypingMessage(timestamp=1, is_typing=True, typing_timestamp=2)
    proto = msg.typing_proto()
    assert proto.action == signalservice_pb2.TypingMessage.STARTED
    assert proto.timestamp == 2
    assert msg.ttl() == 20 * 1000


def test_data_extraction_notification_message_proto():
    msg = DataExtractionNotificationMessage(
        timestamp=3,
        action=signalservice_pb2.DataExtractionNotification.MEDIA_SAVED,
        extraction_timestamp=4,
    )
    proto = msg.data_extraction_proto()
    assert proto.type == signalservice_pb2.DataExtractionNotification.MEDIA_SAVED
    assert proto.timestamp == 4


def test_shared_config_message_proto():
    msg = SharedConfigMessage(
        timestamp=5,
        seqno=7,
        kind=signalservice_pb2.SharedConfigMessage.USER_PROFILE,
        data=b"abc",
    )
    proto = msg.shared_config_proto()
    assert proto.seqno == 7
    assert proto.kind == signalservice_pb2.SharedConfigMessage.USER_PROFILE
    assert proto.data == b"abc"
    assert msg.ttl() == 30 * 24 * 60 * 60 * 1000


def test_message_request_response_proto():
    profile = Profile(display_name="Bob", avatar=Avatar(url="http://filev2.getsession.org/file/1", key=b"k" * 32))
    msg = MessageRequestResponse(timestamp=6, profile=profile)
    proto = msg.message_request_response_proto()
    assert proto.isApproved is True
    assert proto.profile.displayName == "Bob"
    assert proto.profile.profilePicture == profile.avatar.url
    assert proto.profileKey == profile.avatar.key


def test_unsend_message_proto():
    msg = UnsendMessage(timestamp=7, author="alice")
    proto = msg.unsend_proto()
    assert proto.timestamp == 7
    assert proto.author == "alice"
