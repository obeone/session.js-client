# -*- coding: utf-8 -*-

"""
This module defines the Snode namespaces for Session.py.
"""

from enum import IntEnum


class SnodeNamespaces(IntEnum):
    """
    Enum for Snode namespaces.
    """
    UserMessages = 0
    ClosedGroupMessage = 1
    ConvoInfoVolatile = 2
    UserContacts = 3
    UserProfile = 4
    UserGroups = 5
