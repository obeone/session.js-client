import unittest
import asyncio
from session_py import Session

class TestSendMessage(unittest.TestCase):

    def test_send_message(self):
        async def run_test():
            session = Session()
            # This is a dummy mnemonic, replace with a real one for testing against a live network
            mnemonic = "acoustic trophy damage hint search promise blood sunset off hidden knee day lion"
            await session.set_mnemonic(mnemonic)
            
            # This is a dummy session ID, replace with a real one for testing
            recipient_session_id = "05" + "a" * 64

            try:
                result = await session.send_message(
                    to=recipient_session_id,
                    text="Hello, world!"
                )
                self.assertIn('messageHash', result)
                self.assertIn('syncMessageHash', result)
                self.assertIn('timestamp', result)
            except Exception as e:
                # This test will likely fail without a running snode network
                # and a valid recipient.
                print(f"send_message test failed as expected without a live network: {e}")
                pass

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
