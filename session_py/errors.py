# -*- coding: utf-8 -*-

"""
This module contains the set of Session.py's exceptions
"""

from enum import Enum

class SessionException(Exception):
    """
    Base exception class for all Session.py errors.
    """
    def __init__(self, code, message):
        """
        Initializes the SessionException.

        :param code: The error code (can be an Enum member).
        :param message: A descriptive error message.
        """
        self.code = code
        self.message = message
        super().__init__(f"[{self.code.name}] {self.message}")

class SessionValidationErrorCode(Enum):
    """
    Enum for session validation error codes.
    """
    INVALID_OPTIONS = 1
    INVALID_MNEMONIC = 2
    INVALID_SESSION_ID = 3
    INVALID_ATTACHMENT = 4

class SessionValidationError(SessionException):
    """
    Exception raised for validation errors.
    """
    def __init__(self, *, code: SessionValidationErrorCode, message: str):
        """
        Initializes the SessionValidationError.

        :param code: The validation error code (SessionValidationErrorCode).
        :param message: A descriptive error message.
        """
        super().__init__(code, message)

class SessionRuntimeErrorCode(Enum):
    """
    Enum for session runtime error codes.
    """
    NETWORK_NOT_PROVIDED = 1
    EMPTY_USER = 2
    ALREADY_INITIALIZED = 3

class SessionRuntimeError(SessionException):
    """
    Exception raised for runtime errors.
    """
    def __init__(self, *, code: SessionRuntimeErrorCode, message: str):
        """
        Initializes the SessionRuntimeError.

        :param code: The runtime error code (SessionRuntimeErrorCode).
        :param message: A descriptive error message.
        """
        super().__init__(code, message)

class SessionFetchErrorCode(Enum):
    """
    Enum for session fetch error codes.
    """
    SNODE_ERROR = 1
    TIMEOUT = 2
    UNKNOWN = 3

class SessionFetchError(SessionException):
    """
    Exception raised for fetch errors.
    """
    def __init__(self, *, code: SessionFetchErrorCode, message: str):
        """
        Initializes the SessionFetchError.

        :param code: The fetch error code (SessionFetchErrorCode).
        :param message: A descriptive error message.
        """
        super().__init__(code, message)

class SessionCryptoErrorCode(Enum):
    """
    Enum for session crypto error codes.
    """
    MESSAGE_ENCRYPTION_FAILED = 1
    MESSAGE_DECRYPTION_FAILED = 2

class SessionCryptoError(SessionException):
    """
    Exception raised for crypto errors.
    """
    def __init__(self, *, code: SessionCryptoErrorCode, message: str):
        """
        Initializes the SessionCryptoError.

        :param code: The crypto error code (SessionCryptoErrorCode).
        :param message: A descriptive error message.
        """
        super().__init__(code, message)
