# -*- coding: utf-8 -*-

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from session_py.instance.session import Session
from session_py.instance.swarms import get_swarms_for
from session_py.types.snode import Snode
from session_py.types.swarm import Swarm
from session_py.errors import SessionFetchError, SessionFetchErrorCode, SessionRuntimeError, SessionRuntimeErrorCode
from aiohttp.client_reqrep import ConnectionKey

# Fixtures
@pytest.fixture
def mock_session():
    """Fixture for a mocked Session instance."""
    session = MagicMock(spec=Session)
    session.session_id = "test_session_id"
    return session

@pytest.fixture
def mock_snodes():
    """Fixture for a list of mock Snodes."""
    return [
        Snode(host="snode1.com", port=80, pubkey_x25519="pk1", pubkey_ed25519="ed_pk1"),
        Snode(host="snode2.com", port=80, pubkey_x25519="pk2", pubkey_ed25519="ed_pk2"),
        Snode(host="snode3.com", port=80, pubkey_x25519="pk3", pubkey_ed25519="ed_pk3"),
    ]

@pytest.mark.asyncio
async def test_get_swarms_for_success_first_try(mock_session, mock_snodes):
    """
    Test that get_swarms_for succeeds on the first attempt.
    """
    mock_session.get_snodes = AsyncMock(return_value=mock_snodes)
    
    mock_response = {
        "results": [{"body": {"snodes": [{"ip": "1.2.3.4", "port": 1234}]}}]
    }

    with patch('session_py.instance.swarms.do_snode_batch_request', AsyncMock(return_value=mock_response["results"])) as mock_batch_request:
        swarms = await get_swarms_for(mock_session, "some_id")
        
        assert len(swarms) == 1
        assert isinstance(swarms[0], Swarm)
        mock_batch_request.assert_called_once()

@pytest.mark.asyncio
async def test_get_swarms_for_retry_and_succeed(mock_session, mock_snodes):
    """
    Test that get_swarms_for retries on failure and then succeeds.
    """
    mock_session.get_snodes = AsyncMock(return_value=mock_snodes)
    
    mock_success_response = {
        "results": [{"body": {"snodes": [{"ip": "1.2.3.4", "port": 1234}]}}]
    }
    
    # Fail first, then succeed
    side_effects = [
        aiohttp.ClientConnectorError(MagicMock(spec=ConnectionKey), OSError()),
        mock_success_response["results"]
    ]

    with patch('session_py.instance.swarms.do_snode_batch_request', AsyncMock(side_effect=side_effects)) as mock_batch_request:
        swarms = await get_swarms_for(mock_session, "some_id", max_attempts=2, retry_delay=0)
        
        assert len(swarms) == 1
        assert mock_batch_request.call_count == 2

@pytest.mark.asyncio
async def test_get_swarms_for_all_attempts_fail(mock_session, mock_snodes):
    """
    Test that get_swarms_for raises SessionFetchError after all attempts fail.
    """
    mock_session.get_snodes = AsyncMock(return_value=mock_snodes)
    
    side_effects = [
        aiohttp.ClientConnectorError(MagicMock(spec=ConnectionKey), OSError()),
        SessionFetchError(code=SessionFetchErrorCode.SNODE_ERROR, message="421 handled"),
        aiohttp.ServerDisconnectedError()
    ]

    with patch('session_py.instance.swarms.do_snode_batch_request', AsyncMock(side_effect=side_effects)) as mock_batch_request:
        with pytest.raises(SessionFetchError) as excinfo:
            await get_swarms_for(mock_session, "some_id", max_attempts=3, retry_delay=0)
        
        assert "Failed to fetch swarms after 3 attempts" in str(excinfo.value)
        assert mock_batch_request.call_count == 3

@pytest.mark.asyncio
async def test_get_swarms_for_no_snodes_available(mock_session):
    """
    Test that get_swarms_for raises SessionRuntimeError if no snodes are available.
    """
    mock_session.get_snodes = AsyncMock(return_value=[])
    
    with pytest.raises(SessionRuntimeError) as excinfo:
        await get_swarms_for(mock_session, "some_id")
    
    assert excinfo.value.code == SessionRuntimeErrorCode.EMPTY_USER

@pytest.mark.asyncio
async def test_get_swarms_for_ran_out_of_snodes(mock_session, mock_snodes):
    """
    Test that get_swarms_for fails if it runs out of snodes to try.
    """
    # Only provide 2 snodes, but allow 3 attempts
    mock_session.get_snodes = AsyncMock(return_value=mock_snodes[:2])
    
    side_effects = [
        aiohttp.ClientConnectorError(MagicMock(spec=ConnectionKey), OSError()),
        aiohttp.ServerDisconnectedError()
    ]

    with patch('session_py.instance.swarms.do_snode_batch_request', AsyncMock(side_effect=side_effects)) as mock_batch_request:
        with pytest.raises(SessionFetchError):
            await get_swarms_for(mock_session, "some_id", max_attempts=3, retry_delay=0)
        
        # Should only be called twice as there are only 2 snodes
        assert mock_batch_request.call_count == 2
