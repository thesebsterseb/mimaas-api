"""
MIMaaS API Client Authentication

Handles secure token storage and retrieval with proper file permissions.
"""

import os
import stat
from pathlib import Path
from typing import Optional
from .exceptions import AuthenticationError, ConfigurationError


def save_token(token: str, token_file: Optional[Path] = None) -> None:
    """
    Save API token to file with secure permissions (0600).

    Args:
        token: API token to save
        token_file: Path to token file (default: ~/.mimaas/token)

    Raises:
        ConfigurationError: If unable to save token
    """
    if token_file is None:
        token_file = Path("~/.mimaas/token").expanduser()
    else:
        token_file = Path(token_file).expanduser()

    # Create directory if it doesn't exist
    token_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Write token to file
        with open(token_file, 'w') as f:
            f.write(token)

        # Set restrictive permissions (user read/write only)
        token_file.chmod(0o600)

    except Exception as e:
        raise ConfigurationError(f"Failed to save token: {e}")


def load_token(token_file: Optional[Path] = None) -> Optional[str]:
    """
    Load API token from file.

    Args:
        token_file: Path to token file (default: ~/.mimaas/token)

    Returns:
        API token if found, None otherwise

    Raises:
        ConfigurationError: If token file has insecure permissions
    """
    if token_file is None:
        token_file = Path("~/.mimaas/token").expanduser()
    else:
        token_file = Path(token_file).expanduser()

    if not token_file.exists():
        return None

    # Check file permissions (should be 0600)
    file_stat = token_file.stat()
    file_mode = stat.S_IMODE(file_stat.st_mode)

    # Warn if permissions are too permissive (readable by group or others)
    if file_mode & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH):
        # Try to fix permissions
        try:
            token_file.chmod(0o600)
        except Exception:
            raise ConfigurationError(
                f"Token file {token_file} has insecure permissions ({oct(file_mode)}). "
                f"Please run: chmod 600 {token_file}"
            )

    try:
        with open(token_file, 'r') as f:
            token = f.read().strip()
            return token if token else None
    except Exception as e:
        raise ConfigurationError(f"Failed to read token: {e}")


def delete_token(token_file: Optional[Path] = None) -> bool:
    """
    Delete API token file.

    Args:
        token_file: Path to token file (default: ~/.mimaas/token)

    Returns:
        True if deleted, False if file didn't exist
    """
    if token_file is None:
        token_file = Path("~/.mimaas/token").expanduser()
    else:
        token_file = Path(token_file).expanduser()

    if not token_file.exists():
        return False

    try:
        token_file.unlink()
        return True
    except Exception:
        return False


def validate_token_format(token: str) -> bool:
    """
    Validate token format (should be 64-character hex string).

    Args:
        token: Token to validate

    Returns:
        True if valid format, False otherwise
    """
    if not token:
        return False

    # Token should be 64 characters (32 bytes in hex)
    if len(token) != 64:
        return False

    # Should be hexadecimal
    try:
        int(token, 16)
        return True
    except ValueError:
        return False
