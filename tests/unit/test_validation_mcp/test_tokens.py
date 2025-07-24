# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Read INDEX.md files for relevant directories
# 4. Search for rules related to the request
# 5. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""
Unit tests for validation token generation and management following TDD RED phase.
These tests should FAIL initially as the implementation doesn't exist yet.
"""

import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from indexing.test_validation.utils.tokens import ValidationTokenManager


class TestValidationTokens:
    """Test validation token generation, verification, and lifecycle management."""

    def test_token_manager_exists(self):
        """Test that ValidationTokenManager class exists."""
        # This should fail - ValidationTokenManager doesn't exist yet
        assert ValidationTokenManager is not None, "ValidationTokenManager class not implemented yet"

    def test_generate_validation_token(self):
        """Test generating secure validation tokens."""
        # This should fail - generate_token method doesn't exist
        token_manager = ValidationTokenManager()

        test_fingerprint = "abc123def456"
        stage = "design"

        token = token_manager.generate_token(test_fingerprint, stage)

        # Token should be a secure string
        assert isinstance(token, str)
        assert len(token) >= 32  # At least 32 characters for security

        # Should only contain safe characters (alphanumeric, hyphens, underscores)
        assert re.match(r'^[A-Za-z0-9_-]+$', token), "Token contains unsafe characters"

    def test_token_uniqueness(self):
        """Test that each generated token is unique."""
        # This should fail - generate_token method doesn't exist
        # Use higher rate limit to allow 100 tokens for this test
        token_manager = ValidationTokenManager(rate_limit_per_minute=200)

        fingerprint = "test_fingerprint"
        stage = "design"

        # Generate multiple tokens
        tokens = set()
        for _ in range(100):
            token = token_manager.generate_token(fingerprint, stage)
            tokens.add(token)

        # All tokens should be unique
        assert len(tokens) == 100, "Generated tokens are not unique"

    def test_token_validation(self):
        """Test validating tokens against fingerprint and stage."""
        # This should fail - validate_token method doesn't exist
        token_manager = ValidationTokenManager()

        fingerprint = "test_fp_123"
        stage = "implementation"

        # Generate a token
        token = token_manager.generate_token(fingerprint, stage)

        # Validate with correct parameters
        is_valid = token_manager.validate_token(token, fingerprint, stage)
        assert is_valid is True, "Valid token should be accepted"

        # Validate with wrong fingerprint
        is_valid_wrong_fp = token_manager.validate_token(token, "wrong_fp", stage)
        assert is_valid_wrong_fp is False, "Token should be invalid for wrong fingerprint"

        # Validate with wrong stage
        is_valid_wrong_stage = token_manager.validate_token(token, fingerprint, "wrong_stage")
        assert is_valid_wrong_stage is False, "Token should be invalid for wrong stage"

    def test_token_expiration(self):
        """Test that tokens have configurable expiration."""
        # This should fail - expiration functionality doesn't exist
        token_manager = ValidationTokenManager(default_expiry_hours=24)

        fingerprint = "expire_test"
        stage = "design"

        # Generate token with custom expiration
        token = token_manager.generate_token(fingerprint, stage, expires_in_hours=1)

        # Should be valid immediately
        assert token_manager.is_expired(token) is False

        # Check expiration time
        expiry_time = token_manager.get_expiry_time(token)
        expected_expiry = datetime.now() + timedelta(hours=1)

        # Allow 1 minute tolerance for test execution time
        time_diff = abs((expiry_time - expected_expiry).total_seconds())
        assert time_diff < 60, "Expiration time not set correctly"

    def test_token_encoding_decoding(self):
        """Test that tokens can encode and decode metadata."""
        # This should fail - encoding/decoding doesn't exist
        token_manager = ValidationTokenManager()

        fingerprint = "encode_test_fp"
        stage = "breaking"
        user_id = "test_user"

        # Generate token with metadata
        token = token_manager.generate_token(
            fingerprint,
            stage,
            metadata={"user_id": user_id, "priority": "high"}
        )

        # Decode token to extract metadata
        decoded = token_manager.decode_token(token)

        assert decoded["fingerprint"] == fingerprint
        assert decoded["stage"] == stage
        assert decoded["metadata"]["user_id"] == user_id
        assert decoded["metadata"]["priority"] == "high"
        assert "issued_at" in decoded
        assert "expires_at" in decoded

    def test_token_revocation(self):
        """Test revoking tokens to prevent further use."""
        # This should fail - revocation functionality doesn't exist
        token_manager = ValidationTokenManager()

        fingerprint = "revoke_test"
        stage = "approval"

        # Generate and validate token
        token = token_manager.generate_token(fingerprint, stage)
        assert token_manager.validate_token(token, fingerprint, stage) is True

        # Revoke token
        token_manager.revoke_token(token)

        # Should no longer be valid
        assert token_manager.validate_token(token, fingerprint, stage) is False

        # Should show as revoked
        assert token_manager.is_revoked(token) is True

    def test_token_usage_tracking(self):
        """Test tracking token usage for audit purposes."""
        # This should fail - usage tracking doesn't exist
        token_manager = ValidationTokenManager()

        fingerprint = "usage_test"
        stage = "design"

        token = token_manager.generate_token(fingerprint, stage)

        # Mark token as used
        token_manager.mark_used(token, action="test_approved", user="test_user")

        # Check usage information
        usage_info = token_manager.get_usage_info(token)

        assert usage_info["used"] is True
        assert usage_info["action"] == "test_approved"
        assert usage_info["user"] == "test_user"
        assert "used_at" in usage_info

        # Used token should not be usable again
        assert token_manager.validate_token(token, fingerprint, stage) is False

    def test_token_signature_verification(self):
        """Test that tokens have cryptographic signatures."""
        # This should fail - signature verification doesn't exist
        token_manager = ValidationTokenManager(secret_key="test_secret_key_123")

        fingerprint = "signature_test"
        stage = "implementation"

        # Generate token
        token = token_manager.generate_token(fingerprint, stage)

        # Token should have valid signature
        assert token_manager.verify_signature(token) is True

        # Tampered token should fail verification
        tampered_token = token[:-5] + "XXXXX"
        assert token_manager.verify_signature(tampered_token) is False

    def test_token_batch_operations(self):
        """Test generating and managing multiple tokens efficiently."""
        # This should fail - batch operations don't exist
        token_manager = ValidationTokenManager()

        fingerprints = ["fp1", "fp2", "fp3"]
        stage = "design"

        # Generate batch of tokens
        tokens = token_manager.generate_batch(fingerprints, stage)

        assert len(tokens) == 3
        assert all(isinstance(token, str) for token in tokens)
        assert len(set(tokens)) == 3  # All unique

        # Validate batch
        validation_results = token_manager.validate_batch(tokens, fingerprints, [stage] * 3)
        assert all(validation_results), "All tokens should be valid"

        # Revoke batch
        token_manager.revoke_batch(tokens)

        # All should now be invalid
        validation_results_after = token_manager.validate_batch(tokens, fingerprints, [stage] * 3)
        assert not any(validation_results_after), "All tokens should be revoked"

    def test_token_storage_persistence(self):
        """Test that token state persists across manager instances."""
        # This should fail - persistence doesn't exist
        token_manager1 = ValidationTokenManager(storage_path="test_tokens.db")

        fingerprint = "persist_test"
        stage = "approval"

        # Generate token with first manager
        token = token_manager1.generate_token(fingerprint, stage)
        token_manager1.mark_used(token, action="approved", user="test")

        # Create new manager instance
        token_manager2 = ValidationTokenManager(storage_path="test_tokens.db")

        # Should find the token and its usage info
        usage_info = token_manager2.get_usage_info(token)
        assert usage_info["used"] is True
        assert usage_info["action"] == "approved"

        # Cleanup
        token_manager2._cleanup_storage()

    def test_token_cleanup_expired(self):
        """Test automatic cleanup of expired tokens."""
        # This should fail - cleanup functionality doesn't exist
        token_manager = ValidationTokenManager()

        fingerprint = "cleanup_test"
        stage = "design"

        # Generate token with very short expiry
        token = token_manager.generate_token(fingerprint, stage, expires_in_hours=0.001)  # ~3.6 seconds

        # Wait for expiration
        time.sleep(4)

        # Run cleanup
        cleaned_count = token_manager.cleanup_expired()

        assert cleaned_count >= 1, "Should have cleaned up expired token"
        assert token_manager.validate_token(token, fingerprint, stage) is False

    def test_token_security_requirements(self):
        """Test that tokens meet security requirements."""
        # This should fail - security features don't exist
        token_manager = ValidationTokenManager()

        fingerprint = "security_test"
        stage = "breaking"

        token = token_manager.generate_token(fingerprint, stage)

        # Token should have sufficient entropy
        security_analysis = token_manager.analyze_security(token)

        assert security_analysis["entropy_bits"] >= 128, "Token should have high entropy"
        assert security_analysis["character_diversity"] >= 0.7, "Token should use diverse characters"
        assert security_analysis["has_timestamp"] is True, "Token should include timestamp"
        assert security_analysis["has_signature"] is True, "Token should be signed"

    def test_token_rate_limiting(self):
        """Test rate limiting to prevent token abuse."""
        # This should fail - rate limiting doesn't exist
        token_manager = ValidationTokenManager(rate_limit_per_minute=10)

        fingerprint = "rate_limit_test"
        stage = "design"

        # Generate tokens up to limit
        tokens = []
        for i in range(10):
            token = token_manager.generate_token(f"{fingerprint}_{i}", stage)
            tokens.append(token)

        # Next generation should be rate limited
        with pytest.raises(Exception) as exc_info:
            token_manager.generate_token(f"{fingerprint}_overflow", stage)

        assert "rate limit" in str(exc_info.value).lower()


if __name__ == "__main__":
    # Run tests - these should all FAIL in RED phase
    pytest.main([__file__, "-v"])
