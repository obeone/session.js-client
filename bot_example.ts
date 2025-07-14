import { Session, Poller, ready } from './src';
import type { Message } from './src/messages';
import { encode } from '@session.js/mnemonic';
import * as process from 'process';
import { randomBytes } from 'crypto';
import { ProxyNetwork } from './src/network/proxy-network';

/**
 * A simple in-memory storage implementation for the Session client.
 * This is for demonstration purposes only. For a real application,
 * you would use a persistent storage mechanism (e.g., a file or a database).
 */
const inMemoryStorage = {
  storage: new Map<string, string>(),
  get(key: string): string | null {
    return this.storage.get(key) || null;
  },
  set(key: string, value: string): void {
    this.storage.set(key, value);
  },
  delete(key: string): void {
    this.storage.delete(key);
  },
  has(key: string): boolean {
    return this.storage.has(key);
  },
};

/**
 * The main function to initialize and run the bot.
 */
async function main() {
  console.log('Initializing bot...');

  // Wait for the session library to be ready
  await ready;
  console.log('Session library is ready.');

  // 1. Create a new Session instance
  // We pass our in-memory storage implementation.
  // The session will use this to store its keys and other data.
  const proxy = process.env.HTTP_PROXY;
  let network;
  if (proxy) {
    console.log(`Using proxy: ${proxy}`);
    network = new ProxyNetwork(proxy);
  }

  const session = new Session({
    storage: inMemoryStorage,
    network, // if network is undefined, Session will use the default
  });

  // 2. Load or create a mnemonic (seed phrase)
  // This is the bot's identity. We first try to load it from the environment variable.
  // If it doesn't exist, we try to load it from storage.
  // If it's still not found, we create a new one and save it.
  let mnemonic = process.env.MNEMONIC || await session.getMnemonic();
  if (!mnemonic) {
    console.log('No existing mnemonic found. Creating a new one...');
    const seed = randomBytes(16).toString('hex');
    mnemonic = encode(seed);
    await session.setMnemonic(mnemonic);
    console.log('A new mnemonic has been generated. Please save it securely:');
    console.log(`MNEMONIC: ${mnemonic}`);
  } else {
    // If the mnemonic was loaded from the environment variable, set it in the session
    if (process.env.MNEMONIC) {
      await session.setMnemonic(mnemonic);
      console.log('Mnemonic loaded from environment variable.');
    } else {
      console.log('Existing mnemonic loaded from storage.');
    }
  }

  // 3. Get and display the bot's Session ID
  // This is the public address others can use to message the bot.
  const sessionId = session.getSessionID();
  console.log(`Bot is ready. Session ID: ${sessionId}`);
  console.log('Send "ping" to this Session ID to get a reply.');

  // 4. Set up a message handler
  // The 'message' event is fired for every new message received.
  session.on('message', (message: Message) => {
    // We don't want to reply to our own messages
    if (message.from === sessionId) {
      return;
    }

    console.log(`Received message from ${message.from}: "${message.text}"`);

    // Check if the message content is "ping"
    if (message.text && message.text.trim().toLowerCase() === 'ping') {
      console.log(`Received "ping", sending "pong" back to ${message.from}`);
      
      // Send "pong" back to the original sender
      session.sendMessage({
        to: message.from,
        text: 'pong',
      }).catch(console.error);
    }
  });

  // 5. Start the poller
  // The poller is responsible for fetching new messages periodically.
  const poller = new Poller();
  session.addPoller(poller);
  poller.startPolling();

  console.log('Bot is now running and polling for new messages...');
}

// Run the main function and catch any errors.
main().catch(error => {
  console.error('An error occurred during bot execution:', error);
  process.exit(1);
});
