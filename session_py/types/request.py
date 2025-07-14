# -*- coding: utf-8 -*-

"""
This module defines the request types for Session.py.
"""

from enum import Enum

class RequestType(Enum):
    """
    Enum for request types.
    """
    JSON = 'json'
    BINARY = 'binary'
