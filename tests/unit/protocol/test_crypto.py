from pycomap.protocol import crypto


def test_ecdh_roundtrip_produces_matching_shared_secret() -> None:
    alice = crypto.generate_keypair()
    bob = crypto.generate_keypair()

    alice_point = crypto.public_point_bytes(alice)
    bob_point = crypto.public_point_bytes(bob)
    assert len(alice_point) == crypto.EC_POINT_LENGTH
    assert alice_point[0] == 0x04

    secret_from_alice = crypto.shared_secret(alice, bob_point)
    secret_from_bob = crypto.shared_secret(bob, alice_point)
    assert secret_from_alice == secret_from_bob
    assert len(secret_from_alice) == crypto.AES_KEY_LENGTH


def test_derive_key_and_iv_is_deterministic() -> None:
    secret = b"\x01" * 32
    key1, iv1 = crypto.derive_key_and_iv(secret, "0")
    key2, iv2 = crypto.derive_key_and_iv(secret, "0")
    assert key1 == key2
    assert iv1 == iv2
    assert len(key1) == crypto.AES_KEY_LENGTH
    assert len(iv1) == crypto.AES_IV_LENGTH


def test_derive_key_and_iv_differs_per_access_code() -> None:
    secret = b"\x02" * 32
    key_a, iv_a = crypto.derive_key_and_iv(secret, "0")
    key_b, iv_b = crypto.derive_key_and_iv(secret, "1234")
    assert key_a != key_b
    assert iv_a != iv_b


def test_chained_aes_cbc_two_synchronized_instances_roundtrip() -> None:
    """Mirrors the real protocol: both sides derive the same key/IV, then each message's
    IV update is driven by ciphertext bytes both sides observe, in the same order.
    """
    key, iv = crypto.derive_key_and_iv(b"\x03" * 32, "0")
    sender = crypto.ChainedAesCbc(key, iv)
    receiver = crypto.ChainedAesCbc(key, iv)

    for plaintext in (b"first message...", b"second one", b"a third, longer message here"):
        padded = plaintext.ljust((len(plaintext) + 15) // 16 * 16, b"\x00")
        ciphertext = sender.encrypt(padded)
        decrypted = receiver.decrypt(ciphertext)
        assert decrypted == padded
