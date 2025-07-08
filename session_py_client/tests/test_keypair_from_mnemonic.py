from session_py_client import decode_mnemonic, get_keypair_from_seed


def test_mnemonic_to_session_id():
    tests = [
        (
            "session session session session session session session session session session session session session",
            "0512742fb4ac033a8a33f5776aa0e7e88f35f7af9f65dee31e57fbc7d6f8664b12",
        ),
        (
            "love love love love love love love love love love love love love",
            "053db493811f729da20289e31498b8fe2b28edc90358cd3ec11a6b12ac1b9fb818",
        ),
        (
            "puffin luxury annoyed rustled memoir faxed smidgen puddle kiwi nylon utopia zinger kiwi",
            "054830367d369d94605247999a375dbd0a0f65fdec5de1535612bcb6d4de452c69",
        ),
        (
            "unknown number jukebox pledge lipstick sieve tumbling federal womanly outbreak tapestry gorilla sieve",
            "05ab0badfc19ac18f71d7bb10d5ca5c92731aa301cc483169c691cf697b83e765a",
        ),
    ]

    for mnemonic, expected in tests:
        seed = decode_mnemonic(mnemonic)
        kp = get_keypair_from_seed(seed)
        assert kp.x25519.publicKey.hex() == expected

