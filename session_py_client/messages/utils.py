from dataclasses import dataclass

from ..crypto.message_encrypt import EnvelopeType
from ..utils import SessionValidationError, SessionValidationErrorCode

from .base import ContentMessage

@dataclass
class RawMessage:
    '''Representation of a message ready for sending.'''

    identifier: str
    plain_text_buffer: bytes
    recipient: str
    ttl: int
    encryption: EnvelopeType
    namespace: int


def to_raw_message(destination_pub_key: str,
                   message: ContentMessage,
                   namespace: int,
                   is_group: bool = False) -> RawMessage:
    '''
    Convert a :class:`ContentMessage` to :class:`RawMessage`.

    Args:
        destination_pub_key (str): Hex encoded recipient public key.
        message (ContentMessage): Message object.
        namespace (int): Namespace for swarm delivery.
        is_group (bool): ``True`` if message is for a group.

    Returns:
        RawMessage: Prepared raw message structure.
    '''

    ttl = message.ttl()
    if ttl <= 0:
        raise SessionValidationError(
            SessionValidationErrorCode.INVALID_OPTIONS,
            "TTL must be positive",
        )

    encryption = (EnvelopeType.CLOSED_GROUP_MESSAGE
                  if is_group else EnvelopeType.SESSION_MESSAGE)

    return RawMessage(
        identifier=message.identifier,
        plain_text_buffer=message.plain_text_buffer(),
        recipient=destination_pub_key,
        ttl=ttl,
        encryption=encryption,
        namespace=namespace,
    )
