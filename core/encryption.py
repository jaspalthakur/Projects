"""
encryption.py — AES-256-GCM encryption for the local SQLite database file.
Key is derived from the user's master password via Argon2.
"""

import os
import struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


# Salt and nonce sizes
SALT_SIZE = 16
NONCE_SIZE = 12
# Magic header to identify encrypted files
MAGIC = b"PHNTM3"


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a password using Scrypt."""
    kdf = Scrypt(salt=salt, length=32, n=2**17, r=8, p=1)
    return kdf.derive(password.encode("utf-8"))


def encrypt_file(filepath: str, password: str) -> None:
    """
    Encrypt a file in-place with AES-256-GCM.
    The output format: MAGIC | salt(16) | nonce(12) | ciphertext+tag
    """
    with open(filepath, "rb") as f:
        plaintext = f.read()

    # Don't double-encrypt
    if plaintext[:len(MAGIC)] == MAGIC:
        return

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    with open(filepath, "wb") as f:
        f.write(MAGIC)
        f.write(salt)
        f.write(nonce)
        f.write(ciphertext)


def decrypt_file(filepath: str, password: str) -> bool:
    """
    Decrypt a file in-place. Returns True on success, False on wrong password.
    If the file is not encrypted (no magic header), returns True immediately.
    """
    with open(filepath, "rb") as f:
        data = f.read()

    # Not encrypted
    if data[:len(MAGIC)] != MAGIC:
        return True

    pos = len(MAGIC)
    salt = data[pos:pos + SALT_SIZE]
    pos += SALT_SIZE
    nonce = data[pos:pos + NONCE_SIZE]
    pos += NONCE_SIZE
    ciphertext = data[pos:]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        return False  # wrong password or corrupted

    with open(filepath, "wb") as f:
        f.write(plaintext)

    return True


def is_encrypted(filepath: str) -> bool:
    """Check if a file is encrypted (has our magic header)."""
    if not os.path.exists(filepath):
        return False
    with open(filepath, "rb") as f:
        header = f.read(len(MAGIC))
    return header == MAGIC
