"""
security.py — Argon2 password hashing + TOTP 2FA (Time-based One-Time Password).
"""

import io
import argon2
import pyotp
import qrcode
from PIL import Image
from core.constants import APP_NAME


# Argon2 hasher (industry-standard config 2026)
_hasher = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


# ── Password Hashing ──────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password with Argon2id."""
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Verify a password against an Argon2id hash. Returns True on match."""
    try:
        return _hasher.verify(password_hash, password)
    except argon2.exceptions.VerifyMismatchError:
        return False


# ── TOTP 2FA ──────────────────────────────────────────────────────

def generate_totp_secret() -> str:
    """Generate a new random TOTP secret (base32)."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str) -> str:
    """Build an otpauth:// URI for QR code scanning."""
    return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name=APP_NAME)


def verify_totp(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code, with 1-step tolerance."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def generate_qr_pixmap(uri: str) -> Image.Image:
    """Generate a QR code PIL Image from a TOTP URI."""
    qr = qrcode.QRCode(version=1, box_size=8, border=3,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#e6edf3", back_color="#161b22")
    return img.get_image()
