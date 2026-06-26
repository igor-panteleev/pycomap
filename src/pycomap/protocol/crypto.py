"""ECDH handshake and the chained-IV AES-256-CBC cipher used after it.

See ``docs/protocol.md`` section 2.4 (steps 4-9) for the full derivation. The key points
that are easy to get wrong (and were, during reverse-engineering):

- The EC key exchange uses curve secp256r1 (P-256), raw uncompressed point encoding
  (``0x04 || X[32] || Y[32]``).
- The *read* and *write* wire formats for the public key are different: reading the
  controller's key requires skipping a 4-byte prefix; writing ours requires prefixing a
  single length byte. See [pycomap.protocol.client][].
- The AES key/IV are derived via double HMAC-SHA256 keyed by the access code (not the shared
  secret) — see [derive_key_and_iv][].
- There is exactly **one** IV for the whole connection, shared between encryption and
  decryption, advanced after *every* AES operation (either direction) to that operation's
  ciphertext's last 16 bytes. [ChainedAesCbc][] models this with a single internal IV.
"""

from __future__ import annotations

import hashlib
import hmac as _hmac

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher as _CryptoCipher
from cryptography.hazmat.primitives.ciphers import algorithms, modes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

CURVE = ec.SECP256R1()
EC_POINT_LENGTH = 65  # 1 (0x04 prefix) + 32 (X) + 32 (Y)
AES_KEY_LENGTH = 32
AES_IV_LENGTH = 16


def generate_keypair() -> ec.EllipticCurvePrivateKey:
    """Generate a fresh ephemeral keypair on secp256r1."""
    return ec.generate_private_key(CURVE, default_backend())


def public_point_bytes(private_key: ec.EllipticCurvePrivateKey) -> bytes:
    """Raw uncompressed point encoding of ``private_key``'s public key (65 bytes)."""
    return private_key.public_key().public_bytes(
        encoding=Encoding.X962,
        format=PublicFormat.UncompressedPoint,
    )


def shared_secret(private_key: ec.EllipticCurvePrivateKey, peer_point: bytes) -> bytes:
    """Compute the ECDH shared secret (32 bytes) from our private key and the peer's
    raw uncompressed public point.
    """
    peer_key = ec.EllipticCurvePublicKey.from_encoded_point(CURVE, peer_point)
    secret = private_key.exchange(ec.ECDH(), peer_key)
    return secret.rjust(AES_KEY_LENGTH, b"\x00")


def derive_key_and_iv(shared_secret_bytes: bytes, access_code: str) -> tuple[bytes, bytes]:
    """Derive the AES-256 key and initial IV from the ECDH shared secret and access code."""
    access_bytes = access_code.encode("utf-8")
    aes_key = _hmac.new(access_bytes, shared_secret_bytes, hashlib.sha256).digest()
    iv = _hmac.new(access_bytes, aes_key, hashlib.sha256).digest()[:AES_IV_LENGTH]
    return aes_key, iv


class ChainedAesCbc:
    """AES-256-CBC with a single IV shared between encrypt and decrypt, chained on
    ciphertext across the whole connection (see module docstring).
    """

    def __init__(self, key: bytes, iv: bytes) -> None:
        self._key = key
        self._iv = iv

    def encrypt(self, block_payload: bytes) -> bytes:
        """Encrypt an already 16-byte-aligned plaintext payload, advancing the shared IV."""
        encryptor = _CryptoCipher(
            algorithms.AES(self._key), modes.CBC(self._iv), backend=default_backend()
        ).encryptor()
        ciphertext = encryptor.update(block_payload) + encryptor.finalize()
        self._iv = ciphertext[-16:]
        return ciphertext

    def decrypt(self, block_payload: bytes) -> bytes:
        """Decrypt an already 16-byte-aligned ciphertext payload, advancing the shared IV."""
        decryptor = _CryptoCipher(
            algorithms.AES(self._key), modes.CBC(self._iv), backend=default_backend()
        ).decryptor()
        plaintext = decryptor.update(block_payload) + decryptor.finalize()
        self._iv = block_payload[-16:]
        return plaintext
