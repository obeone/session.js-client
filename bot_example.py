#!/usr/bin/env python3
"""
Example bot using session_py library.
This bot listens for incoming messages and auto-replies.
"""

import asyncio
import logging
from session_py import Session, Poller

# Configure logging to show timestamp, level, and message
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(pathname)s - %(message)s'
)

async def main():
    """
    Main entry point for the bot.

    Initializes the session, sets mnemonic, creates poller,
    listens for messages and auto-replies with the received text.
    """
    logging.info("Starting bot...")
    # Replace with your actual 13-word mnemonic
    mnemonic = "hijack cocoa furnished tacit jaunt polar invoke anchor efficient tiger identity opacity cocoa"

    # Initialize session and set mnemonic
    logging.info("Initializing session...")
    session = Session()
    logging.info("Setting mnemonic...")
    await session.set_mnemonic(mnemonic)
    logging.info("Mnemonic set.")

    # Create a poller to listen for incoming messages
    logging.info("Creating poller...")
    poller = Poller(session)
    logging.info("Poller created.")

    @poller.on_message
    def handle_message(message):
        """
        Handles incoming messages.

        :param message: The incoming message data.
        """
        author_id = message['author_session_id']
        text = message['text']
        logging.info(f"Received message from {author_id}: {text}")

        # Auto-reply to the sender
        logging.info(f"Auto-replying to {author_id}...")
        asyncio.create_task(
            session.send_message(
                to=author_id,
                text=f"Vous avez dit : {text}"
            )
        )

    # Start polling for messages (non-blocking)
    logging.info("Starting poller...")
    await poller.start()
    logging.info("Poller started. Bot is now running and waiting for messages.")
    # Keep the script running indefinitely to listen for messages
    while True:
        await asyncio.sleep(3600)  # Sleep for a long time (1 hour)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
