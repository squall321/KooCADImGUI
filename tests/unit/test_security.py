"""Tests for security utilities."""

import tempfile
from pathlib import Path

import pytest

from koocad.utils.security import (
    APIKeyManager,
    ParameterValidator,
    SecretsManager,
    mask_sensitive_data,
)


class TestSecretsManager:
    """Tests for SecretsManager."""

    def test_encrypt_decrypt(self) -> None:
        """Test encryption and decryption."""
        manager = SecretsManager()

        original = "sensitive_data_12345"
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == original
        assert encrypted != original.encode()

    def test_encrypt_bytes(self) -> None:
        """Test encrypting bytes."""
        manager = SecretsManager()

        original = b"binary_data"
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == original.decode()

    def test_save_and_load_key(self) -> None:
        """Test saving and loading encryption key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = Path(tmpdir) / "secret.key"

            # Create manager and save key
            manager1 = SecretsManager()
            manager1.save_key(key_path)

            # Load key in new manager
            manager2 = SecretsManager.from_file(key_path)

            # Should be able to decrypt data encrypted by manager1
            encrypted = manager1.encrypt("test_data")
            decrypted = manager2.decrypt(encrypted)

            assert decrypted == "test_data"


class TestParameterValidator:
    """Tests for ParameterValidator."""

    def test_validate_file_path_safe(self) -> None:
        """Test validating safe file path."""
        assert ParameterValidator.validate_file_path("output/model.step")
        assert ParameterValidator.validate_file_path("data/params.json")

    def test_validate_file_path_traversal(self) -> None:
        """Test detecting path traversal attack."""
        assert not ParameterValidator.validate_file_path("../../../etc/passwd")
        assert not ParameterValidator.validate_file_path("/etc/shadow")

    def test_validate_command_injection_safe(self) -> None:
        """Test validating safe command."""
        assert ParameterValidator.validate_command_injection("model_bga_12mm")
        assert ParameterValidator.validate_command_injection("output.step")

    def test_validate_command_injection_dangerous(self) -> None:
        """Test detecting command injection."""
        assert not ParameterValidator.validate_command_injection("file; rm -rf /")
        assert not ParameterValidator.validate_command_injection("data$(whoami)")
        assert not ParameterValidator.validate_command_injection("test | cat /etc/passwd")

    def test_sanitize_filename(self) -> None:
        """Test filename sanitization."""
        assert ParameterValidator.sanitize_filename("../../secret.txt") == "secret.txt"
        assert ParameterValidator.sanitize_filename("file<>name.step") == "file__name.step"
        assert ParameterValidator.sanitize_filename("C:\\path\\file.txt") == "file.txt"


class TestAPIKeyManager:
    """Tests for APIKeyManager."""

    def test_generate_key(self) -> None:
        """Test API key generation."""
        key1 = APIKeyManager.generate_key()
        key2 = APIKeyManager.generate_key()

        # Should have prefix
        assert key1.startswith("koocad_")
        assert key2.startswith("koocad_")

        # Should be unique
        assert key1 != key2

    def test_generate_key_custom_prefix(self) -> None:
        """Test generating key with custom prefix."""
        key = APIKeyManager.generate_key(prefix="test")
        assert key.startswith("test_")

    def test_hash_and_verify_key(self) -> None:
        """Test hashing and verifying API key."""
        api_key = "koocad_test_key_123"

        # Hash key
        key_hash, salt = APIKeyManager.hash_key(api_key)

        # Verify correct key
        assert APIKeyManager.verify_key(api_key, key_hash, salt)

        # Verify incorrect key
        assert not APIKeyManager.verify_key("wrong_key", key_hash, salt)

    def test_hash_different_salt(self) -> None:
        """Test that different salts produce different hashes."""
        api_key = "koocad_test"

        hash1, salt1 = APIKeyManager.hash_key(api_key)
        hash2, salt2 = APIKeyManager.hash_key(api_key)

        # Different salts
        assert salt1 != salt2

        # Different hashes
        assert hash1 != hash2


class TestMaskSensitiveData:
    """Tests for mask_sensitive_data function."""

    def test_mask_long_string(self) -> None:
        """Test masking long string."""
        data = "koocad_abc123def456ghi789"
        masked = mask_sensitive_data(data, visible_chars=4)

        assert masked.startswith("kooc")
        assert masked.endswith("h789")
        assert "*" in masked

    def test_mask_short_string(self) -> None:
        """Test masking short string."""
        data = "short"
        masked = mask_sensitive_data(data, visible_chars=4)

        # Should be fully masked
        assert masked == "*****"

    def test_mask_custom_visible_chars(self) -> None:
        """Test masking with custom visible characters."""
        data = "0123456789"
        masked = mask_sensitive_data(data, visible_chars=2)

        assert masked == "01******89"
