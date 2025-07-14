# -*- coding: utf-8 -*-

"""
This module defines the request types for the Session network.
"""

from enum import Enum


class RequestType(Enum):
    """
    Enum for the different types of requests that can be made to the Session network.
    """
    GET_SNODES = 'get_snodes'
