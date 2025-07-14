# -*- coding: utf-8 -*-

"""
This module defines the data structures for attachments.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class AttachmentPointer:
    """
    Represents a pointer to an attachment, containing all necessary information
    to retrieve and decrypt it.
    """
    identifier: str
    size: int
    key: bytes
    iv: bytes
    url: str
    digest: str
    mime_type: Optional[str] = None
    file_name: Optional[str] = None
    flags: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    caption: Optional[str] = None
    preview: Optional[bytes] = None
