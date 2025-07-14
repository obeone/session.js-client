import unittest
from session_py.crypto.mnemonic import generate_mnemonic, mnemonic_to_seed, to_keypair

class TestMnemonic(unittest.TestCase):

    def test_generate_mnemonic(self):
        mnemonic = generate_mnemonic()
        self.assertEqual(len(mnemonic.split(' ')), 12)

    def test_mnemonic_to_seed(self):
        mnemonic = "acoustic trophy damage hint search promise blood sunset off hidden knee day lion"
        seed = mnemonic_to_seed(mnemonic)
        self.assertEqual(len(seed), 64)

    def test_to_keypair(self):
        mnemonic = "acoustic trophy damage hint search promise blood sunset off hidden knee day lion"
        seed = mnemonic_to_seed(mnemonic)
        keypair = to_keypair(seed)
        self.assertIsNotNone(keypair.ed25519)
        self.assertIsNotNone(keypair.x25519)
        self.assertEqual(len(keypair.ed25519.pub_key), 32)
        self.assertEqual(len(keypair.ed25519.priv_key), 32)
        self.assertEqual(len(keypair.x25519.pub_key), 32)
        self.assertEqual(len(keypair.x25519.priv_key), 32)

if __name__ == '__main__':
    unittest.main()
