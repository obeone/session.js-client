# -*- coding: utf-8 -*-

"""
This module defines the event types for Session.py.
"""

from typing import Callable, Dict, List, TypeVar, Generic

T = TypeVar('T')

class Event(Generic[T]):
    """
    A simple event class that allows for subscribing and emitting events.
    """
    def __init__(self):
        self._callbacks: List[Callable[[T], None]] = []

    def add_listener(self, callback: Callable[[T], None]):
        """
        Adds a listener to the event.
        """
        self._callbacks.append(callback)

    def remove_listener(self, callback: Callable[[T], None]):
        """
        Removes a listener from the event.
        """
        self._callbacks.remove(callback)

    def emit(self, data: T):
        """
        Emits an event to all subscribed callbacks.
        """
        for callback in self._callbacks:
            callback(data)

# Define specific events
on_message = Event[Dict]()
on_sync_message = Event[Dict]()
on_reaction_added = Event[Dict]()
on_reaction_removed = Event[Dict]()
on_message_deleted = Event[Dict]()
on_message_read = Event[Dict]()
on_message_typing_indicator = Event[Dict]()
on_screenshot_taken = Event[Dict]()
on_media_saved = Event[Dict]()
on_message_request_approved = Event[Dict]()
on_sync_display_name = Event[str]()
on_sync_avatar = Event[Dict]()
on_call = Event[Dict]()
