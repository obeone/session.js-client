# -*- coding: utf-8 -*-

"""
Tests for the Session class.
"""

import pytest
from session_py import Session, Poller
from session_py.errors import SessionRuntimeError

MNEMONIC = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13"
RECIPIENT_MNEMONIC = "word13 word12 word11 word10 word9 word8 word7 word6 word5 word4 word3 word2 word1"

@pytest.fixture
def session():
    """
    Returns a Session instance.
    """
    return Session()

@pytest.fixture
def authorized_session():
    """
    Returns an authorized Session instance.
    """
    s = Session()
    s.set_mnemonic(MNEMONIC)
    return s

@pytest.mark.asyncio
async def test_session_creation(session: Session):
    """
    Tests that a Session instance can be created.
    """
    assert session is not None
    assert session.is_authorized is False

@pytest.mark.asyncio
async def test_get_session_id_uninitialized(session: Session):
    """
    Tests that getting the session ID before initialization raises an error.
    """
    with pytest.raises(SessionRuntimeError):
        session.get_session_id()

@pytest.mark.asyncio
async def test_set_mnemonic(session: Session):
    """
    Tests that setting the mnemonic works correctly.
    """
    session.set_mnemonic(MNEMONIC)
    assert session.is_authorized is True
    assert session.get_mnemonic() == MNEMONIC
    assert session.get_session_id() is not None
    assert session.get_keypair() is not None

@pytest.mark.asyncio
async def test_send_message_unauthorized(session: Session):
    """
    Tests that sending a message without being authorized raises an error.
    """
    with pytest.raises(SessionRuntimeError):
        await session.send_message(to="05" + "a" * 64, text="hello")

@pytest.mark.asyncio
async def test_send_message(authorized_session: Session):
    """
    Tests that sending a message returns a message hash.
    """
    recipient_session = Session()
    recipient_session.set_mnemonic(RECIPIENT_MNEMONIC)
    
    result = await authorized_session.send_message(
        to=recipient_session.get_session_id(),
        text="hello"
    )
    assert result is not None
    assert "messageHash" in result
    assert isinstance(result["messageHash"], str)

@pytest.mark.asyncio
async def test_add_poller(authorized_session: Session):
    """
    Tests that a poller can be added to a session.
    """
    poller = Poller(interval=None) # Disable automatic polling for this test
    authorized_session.add_poller(poller)
    assert poller in authorized_session.pollers
    assert poller.instance == authorized_session
