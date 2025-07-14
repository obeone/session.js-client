import base64
from session_py.crypto.mnemonic import mnemonic_to_seed
from nacl.signing import SigningKey

def test_signature_generation():
    # Values from the TS client logs
    mnemonic = "hijack cocoa furnished tacit jaunt polar invoke anchor efficient tiger identity opacity cocoa"
    
    seed = mnemonic_to_seed(mnemonic)
    
    # The seed for signing is the first 32 bytes of the decoded mnemonic seed.
    signing_key = SigningKey(seed)
    
    # Test vector from the TS client log for namespace 2
    test_vector = {
        'method': 'retrieve',
        'namespace': 2,
        'timestamp': 1752459333155,
        'expected_signature_b64': '9ayAXiTqKrC73t4AqskUQW9s1sA/yQ0aS5u4rsdKrju8kudUZFrPAoQdAsvtlBrFTRNmMRMjb78ijYUmmWpICA==',
        'expected_pubkey_hex': 'ec3fca413647b79fd655706839f139cc72d1de7a1e45b77f27ce483831e8d46e'
    }

    message_str = f"{test_vector['method']}{test_vector['namespace']}{test_vector['timestamp']}"
    message_bytes = message_str.encode('utf-8')

    # Use sign() which returns a SignedMessage object, then access its .signature attribute
    signature_bytes = signing_key.sign(message_bytes).signature
    signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
    
    pubkey_ed25519_hex = bytes(signing_key.verify_key).hex()

    print("--- Python Signature Generation (with library function) ---")
    print(f"Mnemonic: {mnemonic}")
    print(f"Timestamp: {test_vector['timestamp']}")
    print(f"Namespace: {test_vector['namespace']}")
    print(f"Message to sign: {message_str}")
    print(f"Message bytes (hex): {message_bytes.hex()}")
    print(f"Generated Signature (b64): {signature_b64}")
    print(f"Expected Signature (b64):  {test_vector['expected_signature_b64']}")
    print(f"Generated pubkeyEd25519 (hex): {pubkey_ed25519_hex}")
    print(f"Expected pubkeyEd25519 (hex):  {test_vector['expected_pubkey_hex']}")
    print("------------------------------------")

    assert pubkey_ed25519_hex == test_vector['expected_pubkey_hex']
    assert signature_b64 == test_vector['expected_signature_b64']

def test_signature_generation_namespace_0():
    # Values from the TS client logs
    mnemonic = "hijack cocoa furnished tacit jaunt polar invoke anchor efficient tiger identity opacity cocoa"
    
    seed = mnemonic_to_seed(mnemonic)
    
    signing_key = SigningKey(seed)
    
    # Test vector from the TS client log for namespace 0
    test_vector = {
        'method': 'retrieve',
        'namespace': 0,
        'timestamp': 1752459333154,
        'expected_signature_b64': 'c2r6M6xue2MsloA1ocu2WUXVpecDb0fKiC5nhPfV1g+DsDfRSfFMJ9UsulfEIIyrrNv1g/+ZC/T5Z6VvQyEFAQ==',
        'expected_pubkey_hex': 'ec3fca413647b79fd655706839f139cc72d1de7a1e45b77f27ce483831e8d46e'
    }

    message_str = f"{test_vector['method']}{test_vector['timestamp']}"
    message_bytes = message_str.encode('utf-8')

    signature_bytes = signing_key.sign(message_bytes).signature
    signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
    
    pubkey_ed25519_hex = bytes(signing_key.verify_key).hex()

    assert pubkey_ed25519_hex == test_vector['expected_pubkey_hex']
    assert signature_b64 == test_vector['expected_signature_b64']

def test_x25519_key_derivation():
    from session_py.crypto.mnemonic import to_keypair
    mnemonic = "hijack cocoa furnished tacit jaunt polar invoke anchor efficient tiger identity opacity cocoa"
    seed = mnemonic_to_seed(mnemonic)
    keypair = to_keypair(seed)
    
    expected_x25519_pubkey_hex = "d817255499c77684e7ad518b079dd8dbb133922b71632c37e57b98246d82bf72"
    
    assert keypair.x25519.pub_key.hex() == expected_x25519_pubkey_hex

if __name__ == "__main__":
    test_signature_generation()
    test_signature_generation_namespace_0()
    test_x25519_key_derivation()
