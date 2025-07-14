# -*- coding: utf-8 -*-

"""
This module defines the Poller class for Session.py.
"""

import asyncio
import json
import random
import time
from typing import TYPE_CHECKING, Optional, Callable, List, Dict, Any
from session_py.errors import SessionRuntimeError, SessionRuntimeErrorCode
from session_py.network.base import Request
from session_py.types.namespaces import SnodeNamespaces
from session_py.crypto.message_decrypt import decrypt
from session_py.crypto.signature import sign_request
from session_py.messages.schema.signal import Signal, Content, DataMessage
from session_py.utils import base64_to_bytes, bytes_to_hex
from session_py.logs import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from session_py.instance.session import Session


class Poller:
    """
    A class that polls for new messages from the Session network.
    """

    def __init__(self, session: 'Session', interval: int = 3000):
        """
        Initializes the Poller.

        :param session: The Session instance to poll.
        :param interval: Polling interval in milliseconds.
        """
        self.session = session
        self.interval = interval
        self.polling = False
        self.task: Optional[asyncio.Task] = None
        self.on_message_callbacks: List[Callable] = []

    def on_message(self, func: Callable):
        """
        Decorator to register a message handler callback.

        :param func: The callback function to handle messages.
        :return: The original function.
        """
        self.on_message_callbacks.append(func)
        return func

    async def start(self):
        """
        Starts the polling loop asynchronously.
        """
        if not self.session.is_authorized:
            raise SessionRuntimeError(
                code=SessionRuntimeErrorCode.EMPTY_USER,
                message='Polling can\'t be started without an authorized session'
            )
        if not self.polling:
            self.polling = True
            self.task = asyncio.create_task(self._poll_loop())

    def stop(self):
        """
        Stops the polling loop.
        """
        if self.polling and self.task:
            self.polling = False
            self.task.cancel()
            self.task = None

    async def _poll_loop(self):
        """
        Internal method that runs the polling loop.
        """
        while self.polling:
            try:
                await self.poll()
            except Exception as e:
                logger.exception("Error during polling: %s", e)
            await asyncio.sleep(self.interval / 1000)

    async def poll(self) -> List[DataMessage]:
        """
        Manually triggers a poll for new messages.

        :return: A list of decrypted DataMessage objects.
        """
        if not self.session.keypair:
            raise SessionRuntimeError(code=SessionRuntimeErrorCode.EMPTY_USER, message='Polling requires a keypair')

        our_swarm = await self.session.get_our_swarm()
        if not our_swarm:
            return []

        snode = random.choice(our_swarm.snodes)
        
        namespaces = [
            SnodeNamespaces.UserMessages,
            SnodeNamespaces.ConvoInfoVolatile,
            SnodeNamespaces.UserContacts,
            SnodeNamespaces.UserGroups,
            SnodeNamespaces.UserProfile
        ]

        subrequests = []
        for namespace in namespaces:
            timestamp = int(time.time() * 1000)
            last_hash = await self.session.storage.get(f'last_hash_{namespace.value}') or ''
            signature_params = sign_request(
                keypair=self.session.keypair,
                method='retrieve',
                namespace=namespace.value,
                timestamp=timestamp
            )

            subrequests.append({
                "method": "retrieve",
                "params": {
                    "pubkey": self.session.get_session_id(),
                    "namespace": namespace.value,
                    "last_hash": last_hash,
                    "timestamp": timestamp,
                    **signature_params
                }
            })

        logger.debug(f"Subrequests for batch: {json.dumps(subrequests, indent=2)}")

        from session_py.instance.snode_batch import do_snode_batch_request
        
        batch_result = await do_snode_batch_request(
            url=f"https://{snode.host}:{snode.port}/storage_rpc/v1",
            subrequests=subrequests,
            timeout=10
        )

        all_messages = []
        for i, sub_resp in enumerate(batch_result):
            if sub_resp.get('code') != 200:
                logger.warning(f"Sub-request for namespace {namespaces[i].value} failed with code {sub_resp.get('code')}")
                continue

            raw_messages = sub_resp.get('body', {}).get('messages', [])
            decrypted_messages: List[DataMessage] = []

            for raw_msg in raw_messages:
                try:
                    ciphertext = base64_to_bytes(raw_msg['data'])
                    plaintext_bytes = decrypt(
                        recipient_keypair=self.session.keypair,
                        ciphertext=ciphertext,
                        envelope_type=Signal.Type.SESSION_MESSAGE,
                        sender_x25519_pubkey_hex=raw_msg['pubkey']
                    )
                    content = Content.decode(plaintext_bytes)
                    if content.dataMessage:
                        message = content.dataMessage
                        message.author_session_id = raw_msg['pubkey']
                        decrypted_messages.append(message)
                        for callback in self.on_message_callbacks:
                            callback(message)
                except Exception as e:
                    print(f"Failed to decrypt message: {e}")

            if raw_messages:
                new_last_hash = raw_messages[-1]['hash']
                await self.session.storage.set(f'last_hash_{namespaces[i].value}', new_last_hash)
            
            all_messages.extend(decrypted_messages)

        # Convert DataMessage objects to dictionaries for on_messages_received
        messages_as_dicts = [vars(msg) for msg in all_messages]
        await self.session.on_messages_received(messages_as_dicts)
        return all_messages
