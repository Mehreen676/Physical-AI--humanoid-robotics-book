"""
TOTP Multi-Factor Authentication Utilities (Phase 6).
Handles TOTP secret generation, verification, QR code generation, and backup codes.
"""

import pyotp
import qrcode
import io
import base64
import secrets
import string
from typing import List, Tuple
import bcrypt
import logging

logger = logging.getLogger(__name__)


def generate_totp_secret() -> str:
    """
    Generate a random TOTP secret.

    Returns:
        str: Base32-encoded TOTP secret (32 characters)
    """
    return pyotp.random_base32()


def generate_qr_code(secret: str, user_email: str, issuer_name: str = "RAG-Chatbot") -> str:
    """
    Generate QR code for TOTP setup.

    Args:
        secret: Base32-encoded TOTP secret
        user_email: User's email address
        issuer_name: Name of the application/issuer

    Returns:
        str: Base64-encoded PNG image of QR code
    """
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user_email, issuer_name=issuer_name)

    # Generate QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    # Convert to image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64 PNG
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_base64 = base64.b64encode(buf.getvalue()).decode()

    return f"data:image/png;base64,{img_base64}"


def verify_totp_code(secret: str, code: str, time_step: int = 30, window: int = 1) -> bool:
    """
    Verify a TOTP code against the secret.

    Args:
        secret: Base32-encoded TOTP secret
        code: 6-digit code from authenticator app
        time_step: TOTP time step in seconds (default 30)
        window: Number of time steps to check before/after current (default 1 = ±30s)

    Returns:
        bool: True if code is valid, False otherwise

    Note:
        Window of 1 allows ±30 seconds of tolerance for clock skew
    """
    try:
        totp = pyotp.TOTP(secret, interval=time_step)
        return totp.verify(code, valid_window=window)
    except Exception as e:
        logger.error(f"TOTP verification error: {e}")
        return False


def generate_backup_codes(count: int = 10, code_length: int = 8) -> List[str]:
    """
    Generate backup codes for account recovery.

    Args:
        count: Number of backup codes to generate (default 10)
        code_length: Length of each code (default 8)

    Returns:
        List[str]: List of backup codes (unhashed, show to user)

    Note:
        Codes are alphanumeric uppercase, exclude confusing characters (0, O, I, l)
    """
    # Remove confusing characters
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace("0", "").replace("O", "").replace("I", "").replace("l", "")

    backup_codes = []
    for _ in range(count):
        code = "".join(secrets.choice(chars) for _ in range(code_length))
        backup_codes.append(code)

    return backup_codes


def hash_backup_code(code: str) -> str:
    """
    Hash a backup code using bcrypt (one-way, for storage).

    Args:
        code: Plaintext backup code

    Returns:
        str: Hashed backup code

    Note:
        Uses bcrypt with 12 rounds for consistent security with password hashing
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(code.encode(), salt)
    return hashed.decode()


def verify_backup_code(code: str, hashed_code: str) -> bool:
    """
    Verify a backup code against its hash.

    Args:
        code: Plaintext backup code from user
        hashed_code: Hashed backup code from database

    Returns:
        bool: True if code matches hash, False otherwise
    """
    try:
        return bcrypt.checkpw(code.encode(), hashed_code.encode())
    except Exception as e:
        logger.error(f"Backup code verification error: {e}")
        return False


def hash_backup_codes(codes: List[str]) -> List[str]:
    """
    Hash a list of backup codes for storage.

    Args:
        codes: List of plaintext backup codes

    Returns:
        List[str]: List of hashed backup codes
    """
    return [hash_backup_code(code) for code in codes]


def validate_totp_code_format(code: str) -> bool:
    """
    Validate that a code is in proper TOTP format (6 digits).

    Args:
        code: Code to validate

    Returns:
        bool: True if valid format, False otherwise
    """
    return isinstance(code, str) and len(code) == 6 and code.isdigit()
