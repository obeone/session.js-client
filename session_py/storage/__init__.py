# -*- coding: utf-8 -*-

"""
This package provides storage implementations for Session.py.
"""

from .base import Storage
from .file import FileStorage

__all__ = [
    'Storage',
    'FileStorage'
]
