"""
Security utilities for KooCAD.

This module provides utilities for secrets management, encryption,
and secure parameter handling.
"""

import hashlib
import hmac
import secrets
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet


class SecretsManager:
    """Manage encrypted secrets and sensitive parameters.

    Example:
        >>> manager = SecretsManager()
        >>> encrypted = manager.encrypt("sensitive_data")
        >>> decrypted = manager.decrypt(encrypted)
    """

    def __init__(self, key: Optional[bytes] = None) -> None:
        """Initialize secrets manager.

        Args:
            key: Encryption key (generated if not provided).
        """
        if key is None:
            key = Fernet.generate_key()
        self.cipher = Fernet(key)
        self.key = key

    @classmethod
    def from_file(cls, key_path: str | Path) -> "SecretsManager":
        """Load encryption key from file.

        Args:
            key_path: Path to key file.

        Returns:
            SecretsManager instance.

        Example:
            >>> manager = SecretsManager.from_file(".koocad/secret.key")
        """
        key_path = Path(key_path)
        key = key_path.read_bytes()
        return cls(key=key)

    def encrypt(self, data: str | bytes) -> bytes:
        """Encrypt data.

        Args:
            data: Data to encrypt (string or bytes).

        Returns:
            Encrypted data as bytes.
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        return self.cipher.encrypt(data)

    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data.

        Args:
            encrypted_data: Encrypted data.

        Returns:
            Decrypted data as string.
        """
        decrypted = self.cipher.decrypt(encrypted_data)
        return decrypted.decode("utf-8")

    def save_key(self, key_path: str | Path) -> None:
        """Save encryption key to file.

        Args:
            key_path: Path to save key file.
        """
        key_path = Path(key_path)
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_bytes(self.key)
        key_path.chmod(0o600)  # Read/write for owner only


class ParameterValidator:
    """Validate parameters for security vulnerabilities."""

    @staticmethod
    def validate_file_path(path: str) -> bool:
        """Validate file path for path traversal attacks.

        Args:
            path: File path to validate.

        Returns:
            True if path is safe, False otherwise.

        Example:
            >>> ParameterValidator.validate_file_path("../../../etc/passwd")
            False
            >>> ParameterValidator.validate_file_path("output/model.step")
            True
        """
        path_obj = Path(path).resolve()

        # Check for path traversal
        try:
            # Ensure path doesn't escape working directory
            path_obj.relative_to(Path.cwd())
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_command_injection(value: str) -> bool:
        """Check for potential command injection.

        Args:
            value: String to check.

        Returns:
            True if safe, False if suspicious.
        """
        dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">"]
        return not any(char in value for char in dangerous_chars)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal.

        Args:
            filename: Original filename.

        Returns:
            Sanitized filename.

        Example:
            >>> ParameterValidator.sanitize_filename("../../secret.txt")
            'secret.txt'
        """
        # Remove directory components
        filename = Path(filename).name

        # Remove dangerous characters
        dangerous = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
        for char in dangerous:
            filename = filename.replace(char, "_")

        return filename


class APIKeyManager:
    """Manage API keys for authentication."""

    @staticmethod
    def generate_key(prefix: str = "koocad", length: int = 32) -> str:
        """Generate a secure API key.

        Args:
            prefix: Key prefix for identification.
            length: Length of random part (bytes).

        Returns:
            API key string.

        Example:
            >>> key = APIKeyManager.generate_key()
            >>> assert key.startswith("koocad_")
        """
        random_part = secrets.token_urlsafe(length)
        return f"{prefix}_{random_part}"

    @staticmethod
    def hash_key(api_key: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """Hash API key for storage.

        Args:
            api_key: API key to hash.
            salt: Salt for hashing (generated if not provided).

        Returns:
            Tuple of (hash, salt).

        Example:
            >>> key_hash, salt = APIKeyManager.hash_key("koocad_abc123")
        """
        if salt is None:
            salt = secrets.token_bytes(32)

        key_hash = hashlib.pbkdf2_hmac(
            "sha256",
            api_key.encode("utf-8"),
            salt,
            iterations=100000,
        )

        return key_hash, salt

    @staticmethod
    def verify_key(api_key: str, stored_hash: bytes, salt: bytes) -> bool:
        """Verify API key against stored hash.

        Args:
            api_key: API key to verify.
            stored_hash: Stored hash from database.
            salt: Salt used for hashing.

        Returns:
            True if key is valid.
        """
        key_hash, _ = APIKeyManager.hash_key(api_key, salt)
        return hmac.compare_digest(key_hash, stored_hash)


class AuditLogger:
    """Log security-relevant events."""

    def __init__(self, log_file: Optional[Path] = None) -> None:
        """Initialize audit logger.

        Args:
            log_file: Path to audit log file.
        """
        self.log_file = log_file or Path("audit.log")

    def log_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log resource access attempt.

        Args:
            user_id: User identifier.
            resource: Resource being accessed.
            action: Action being performed.
            success: Whether access was granted.
            metadata: Additional metadata.
        """
        import json
        import time

        entry = {
            "timestamp": time.time(),
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "success": success,
            "metadata": metadata or {},
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_parameter_change(
        self,
        user_id: str,
        parameter_name: str,
        old_value: Any,
        new_value: Any,
    ) -> None:
        """Log parameter modification.

        Args:
            user_id: User making the change.
            parameter_name: Name of parameter.
            old_value: Previous value.
            new_value: New value.
        """
        self.log_access(
            user_id=user_id,
            resource=f"parameter:{parameter_name}",
            action="modify",
            success=True,
            metadata={
                "old_value": str(old_value),
                "new_value": str(new_value),
            },
        )


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data for logging.

    Args:
        data: Sensitive data to mask.
        visible_chars: Number of characters to leave visible.

    Returns:
        Masked string.

    Example:
        >>> mask_sensitive_data("koocad_abc123def456", visible_chars=4)
        'kooc************f456'
    """
    if len(data) <= visible_chars * 2:
        return "*" * len(data)

    prefix = data[:visible_chars]
    suffix = data[-visible_chars:]
    mask_length = len(data) - visible_chars * 2

    return f"{prefix}{'*' * mask_length}{suffix}"
