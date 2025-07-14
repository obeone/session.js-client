# -*- coding: utf-8 -*-

"""
This module defines the Swarm type for Session.py.
"""

from dataclasses import dataclass
from typing import List
from .snode import Snode

@dataclass
class Swarm:
    """
    Represents a Swarm.
    """
    snodes: List[Snode]
