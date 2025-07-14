# -*- coding: utf-8 -*-

"""
This module defines the main Session class.
"""
import time
from typing import Optional, Set, Any
from email.utils import parsedate_to_datetime
from session_py.storage.base import Storage
from session_py.network.base import Network, Request, Response
from session_py.network.request import RequestType
from session_py.crypto.keypair import Keypair
from session_py.types.snode import Snode
from session_py.types.swarm import Swarm
from session_py.polling.poller import Poller
from session_py.storage.memory import InMemoryStorage
from session_py.network.aiohttp_backend import AiohttpNetwork
from session_py.errors import SessionRuntimeError, SessionRuntimeErrorCode
from session_py.logs import get_logger
from .get_set_mnemonic import set_mnemonic, get_mnemonic
from .send_message import send_message
from session_py.instance.snodes import get_snodes
from .swarms import get_swarms_for, get_our_swarm
from .store_message import _store_message
from .polling import on_messages_received, on_swarm_connection_failed
from . import events
logger = get_logger(__name__)

class Session:
    """
    The main class for interacting with the Session network.
    """

    def __init__(self, storage: Optional[Storage] = None, network: Optional[Network] = None, proxy: Optional[str] = None):
        self.storage = storage if storage is not None else InMemoryStorage()
        self.network = network if network is not None else AiohttpNetwork(proxy=proxy)
        self.mnemonic: Optional[str] = None
        self.keypair: Optional[Keypair] = None
        self.session_id: Optional[str] = None
        self.display_name: Optional[str] = None
        self.avatar: Optional[dict] = None
        self.snodes: Optional[list[Snode]] = None
        self.our_swarms: Optional[list[Swarm]] = None
        self.our_swarm: Optional[Swarm] = None
        self.pollers: Set[Poller] = set()
        self._network_offset: float = 0.0
        self.is_authorized: bool = False
        self.on_message = events.Event()
        self.on_sync_message = events.Event()

    async def _request(self, req: Request) -> Response:
        return await self.network.on_request(req)

    async def _init(self):
        """
        Performs asynchronous initialization tasks for the session,
        such as loading saved data and synchronizing network time.
        """
        saved_avatar = await self.storage.get('avatar')
        if saved_avatar:
            import json
            key, url = json.loads(saved_avatar).values()
            self.avatar = {'key': bytes(key), 'url': url}

        try:
            snodes = await self.get_snodes()
            if snodes:
                snode = snodes[0]
                url = f"https://{snode.host}:{snode.port}/storage_rpc/v1"
                req = Request(url=url, method='HEAD')
                resp = await self.network.on_request(req)
                if 'Date' in resp.headers:
                    server_time = parsedate_to_datetime(resp.headers['Date']).timestamp()
                    self._network_offset = server_time - time.time()
        except Exception:
            # Gracefully fail if we can't get the network time
            pass

    def _emit(self, event_name: str, data: Any):
        """
        Emits a specified event with the given data.

        :param event_name: The name of the event to emit (e.g., 'message').
        :param data: The data to pass to the event listeners.
        """
        if hasattr(self, f'on_{event_name}'):
            getattr(self, f'on_{event_name}').emit(data)

    set_mnemonic = set_mnemonic
    get_mnemonic = get_mnemonic
    send_message = send_message
    get_snodes = get_snodes
    get_swarms_for = get_swarms_for
    get_our_swarm = get_our_swarm
    _store_message = _store_message
    on_messages_received = on_messages_received
    on_swarm_connection_failed = on_swarm_connection_failed

    def get_now_with_network_offset(self) -> float:
        """
        Returns the current timestamp, adjusted by the network offset.
        This provides a time that is synchronized with the Session network.
        """
        return time.time() + self._network_offset

    def get_session_id(self) -> str:
        """
        Returns the session ID of this instance.
        :raises SessionRuntimeError: if the user is not set yet.
        """
        if not self.session_id:
            raise SessionRuntimeError(
                code=SessionRuntimeErrorCode.EMPTY_USER,
                message='Instance is not initialized; use set_mnemonic first'
            )
        return self.session_id

    def get_display_name(self) -> Optional[str]:
        """
        Get the cached display name of this instance.
        """
        return self.display_name

    def get_avatar(self) -> Optional[dict]:
        """
        Get this instance's cached avatar.
        """
        return self.avatar

    def get_keypair(self) -> Optional[Keypair]:
        """
        Returns the keypair of this instance.
        """
        return self.keypair
