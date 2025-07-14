#!/usr/bin/env python3
"""
This script generates a new Session account mnemonic and displays the corresponding Session ID.
"""

import asyncio
from session_py import Session
from session_py.crypto.mnemonic import generate_mnemonic


async def create_account():
    """
    Generates a new mnemonic, initializes a session, and prints the account details.
    """
    # Generate a new mnemonic
    new_mnemonic = generate_mnemonic()

    # Initialize a new session
    session = Session()

    # Set the mnemonic for the session. This derives the keys and Session ID.
    await session.set_mnemonic(new_mnemonic)

    print("--- New Session Account Created ---")
    print("\nGenerated Mnemonic (SAVE THIS!):")
    print(new_mnemonic)
    print("\nYour new Session ID:")
    print(session.session_id)
    print("\n------------------------------------")
    print("You can now use this mnemonic in your bot_example.py script.")


if __name__ == "__main__":
    try:
        asyncio.run(create_account())
    except KeyboardInterrupt:
        print("Exiting...")
