# -*- coding: utf-8 -*-

"""
This module provides logging configuration for the Session.py library.
"""

import logging
import sys
from logging import Logger

# 1. Create a logger
logger = logging.getLogger('session_py')
logger.setLevel(logging.DEBUG)
logger.propagate = False

# 2. Create a handler
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG) # Set handler level to DEBUG

# 3. Create a formatter and add it to the handler
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

# 4. Add the handler to the logger
if not logger.handlers:
    logger.addHandler(handler)


def get_logger(name: str) -> Logger:
    """
    Returns a logger with the specified name.
    This is a child of the main 'session_py' logger.

    :param name: The name of the logger (e.g., 'instance', 'polling').
    :return: A logger instance.
    """
    return logging.getLogger(f'session_py.{name}')
