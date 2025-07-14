# -*- coding: utf-8 -*-

"""
This module defines the schema for visible messages.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from session_py.types.attachment import AttachmentPointer

@dataclass
class Quote:
    """
    Represents a quoted message.
    """
    id: int
    author: str
    text: Optional[str] = None
    attachments: List[AttachmentPointer] = field(default_factory=list)

@dataclass
class VisibleMessage:
    """
    Represents a visible message.
    """
    body: Optional[str] = None
    profile: Optional[dict] = None
    timestamp: int = 0
    expirationType: str = 'unknown'
    expireTimer: int = 0
    identifier: str = ''
    attachments: List[AttachmentPointer] = field(default_factory=list)
    preview: list = field(default_factory=list)
    quote: Optional[Quote] = None
    syncTarget: Optional[str] = None
    reaction: Optional[dict] = None
