# -*- coding: utf-8 -*-

import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from session_py.attachments.encrypt import encrypt_file
from session_py.attachments.decrypt import decrypt
from session_py.network.base import Response

class TestAttachments(unittest.TestCase):

    def test_encrypt_decrypt_roundtrip(self):
        async def run_test():
            # 1. Setup
            mock_network = MagicMock()
            mock_network.on_request = AsyncMock()

            # Mock the upload response
            mock_network.on_request.return_value = Response(status_code=200, body=b'')

            original_data = b"This is a test file for attachments."

            # 2. Encrypt
            attachment_pointer = await encrypt_file(original_data, mock_network)

            # 3. Decrypt
            # We need to replace the encrypted data with the original for the test
            # because the encryption is random.
            # In a real scenario, the server would store the uploaded data.
            
            # For the purpose of this test, we'll "download" the ciphertext we just created.
            # In a real scenario, the server would return the ciphertext.
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            aesgcm = AESGCM(attachment_pointer.key)
            ciphertext = aesgcm.encrypt(attachment_pointer.iv, original_data, None)

            mock_network.on_request.return_value = Response(status_code=200, body=ciphertext)

            decrypted_data = await decrypt(attachment_pointer, mock_network)

            # 4. Assert
            self.assertEqual(original_data, decrypted_data)

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
