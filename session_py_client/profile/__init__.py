from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
import os

PROFILE_IV_LENGTH = 12  # bytes
PROFILE_KEY_LENGTH = 32  # bytes
PROFILE_TAG_LENGTH = 128  # bits

from .encrypt import encrypt_profile
from .decrypt import decrypt_profile


@dataclass
class Avatar:
    url: str
    key: bytes


@dataclass
class Profile:
    display_name: str
    avatar: Optional[Avatar] = None


def serialize_profile(profile: Profile) -> Dict[str, Any]:
    '''
    Serialize a Profile instance into a dictionary.

    Args:
        profile (Profile): Profile instance to serialize.

    Returns:
        Dict[str, Any]: Dictionary with ``lokiProfile`` and ``profileKey`` fields.
    '''
    signal_profile = None
    if profile.avatar or profile.display_name:
        signal_profile = {}
        if profile.avatar and profile.avatar.url and len(profile.avatar.key):
            signal_profile["profilePicture"] = profile.avatar.url
        if profile.display_name:
            signal_profile["displayName"] = profile.display_name

    return {
        "lokiProfile": signal_profile,
        "profileKey": profile.avatar.key if profile.avatar else None,
    }


def deserialize_profile(data: Dict[str, Any]) -> Profile:
    '''
    Create a Profile instance from serialized data.

    Args:
        data (Dict[str, Any]): Serialized profile dictionary.

    Returns:
        Profile: Restored profile object.
    '''
    loki_profile = data.get("lokiProfile") or {}
    display_name = loki_profile.get("displayName", "")
    avatar = None
    avatar_url = loki_profile.get("profilePicture")
    profile_key = data.get("profileKey")
    if avatar_url and profile_key:
        avatar = Avatar(url=avatar_url, key=profile_key)
    return Profile(display_name=display_name, avatar=avatar)


async def download_avatar(self, avatar: Avatar) -> bytes:
    '''
    Download and decrypt avatar image using Session network.

    Args:
        self: Session-like object with ``_request`` coroutine.
        avatar (Avatar): Avatar descriptor with ``url`` and ``key``.

    Returns:
        bytes: Decrypted avatar image.
    '''
    file_server_url = "http://filev2.getsession.org/file/"
    if not avatar.url.startswith(file_server_url):
        raise ValueError("Avatar must be hosted on Session file server")

    file_id = avatar.url[len(file_server_url) :]
    if not file_id.isdigit():
        raise ValueError("Invalid avatar file ID")

    avatar_file = await self._request(
        {
            "type": "DownloadAttachment",
            "body": {"id": file_id},
        }
    )
    return decrypt_profile(avatar_file, avatar.key)


async def upload_avatar(self, avatar: bytes) -> Dict[str, Any]:
    '''
    Encrypt and upload avatar to the file server.

    Args:
        self: Session-like object with ``_request`` coroutine.
        avatar (bytes): Raw avatar image.

    Returns:
        Dict[str, Any]: Dictionary with ``profileKey`` and ``avatarPointer``.
    '''
    profile_key = os.urandom(PROFILE_KEY_LENGTH)
    encrypted_avatar = encrypt_profile(avatar, profile_key)
    upload_request = await self._request(
        {
            "type": "UploadAttachment",
            "body": {"data": encrypted_avatar},
        }
    )
    return {"profileKey": profile_key, "avatarPointer": upload_request["url"]}

__all__ = [
    "PROFILE_IV_LENGTH",
    "PROFILE_KEY_LENGTH",
    "PROFILE_TAG_LENGTH",
    "Avatar",
    "Profile",
    "serialize_profile",
    "deserialize_profile",
    "encrypt_profile",
    "decrypt_profile",
    "download_avatar",
    "upload_avatar",
]
