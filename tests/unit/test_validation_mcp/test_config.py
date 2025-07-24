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
Unit tests for configuration management following TDD RED phase.
These tests should FAIL initially as the implementation doesn't exist yet.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from indexing.test_validation.utils.config import ValidationConfig


class TestValidationConfig:
    """Test configuration loading and management for test validation system."""

    def test_config_manager_exists(self):
        """Test that ValidationConfig class exists."""
        # This should fail - ValidationConfig doesn't exist yet
        assert ValidationConfig is not None, "ValidationConfig class not implemented yet"

    def test_load_default_config(self):
        """Test loading default configuration values."""
        # This should fail - load_defaults method doesn't exist
        config = ValidationConfig()

        # Should have default values
        defaults = config.get_defaults()

        assert isinstance(defaults, dict)
        assert "database_path" in defaults
        assert "token_expiry_hours" in defaults
        assert "max_validation_attempts" in defaults
        assert "gemini_model" in defaults
        assert "validation_stages" in defaults

        # Check specific defaults
        assert defaults["token_expiry_hours"] == 168  # 7 days
        assert defaults["max_validation_attempts"] == 3
        assert defaults["gemini_model"] == "gemini-2.5-flash"
        assert "design" in defaults["validation_stages"]

    def test_load_config_from_file(self):
        """Test loading configuration from JSON file."""
        # This should fail - load_from_file method doesn't exist
        config_data = {
            "database_path": "/custom/path/validation.db",
            "token_expiry_hours": 48,
            "gemini_model": "gemini-2.5-pro",
            "rate_limit_per_minute": 20,
            "debug_mode": True
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = ValidationConfig.load_from_file(config_path)

            assert config.get("database_path") == "/custom/path/validation.db"
            assert config.get("token_expiry_hours") == 48
            assert config.get("gemini_model") == "gemini-2.5-pro"
            assert config.get("debug_mode") is True
        finally:
            os.unlink(config_path)

    def test_environment_variable_overrides(self):
        """Test that environment variables override config values."""
        # This should fail - environment override functionality doesn't exist
        config = ValidationConfig()

        # Set environment variables
        os.environ["TEST_VALIDATION_DB_PATH"] = "/env/override/path.db"
        os.environ["TEST_VALIDATION_TOKEN_EXPIRY"] = "96"
        os.environ["TEST_VALIDATION_DEBUG"] = "true"

        try:
            # Load config with env overrides
            config.load_with_env_overrides(prefix="TEST_VALIDATION_")

            assert config.get("database_path") == "/env/override/path.db"
            assert config.get("token_expiry_hours") == 96
            assert config.get("debug_mode") is True
        finally:
            # Cleanup environment
            del os.environ["TEST_VALIDATION_DB_PATH"]
            del os.environ["TEST_VALIDATION_TOKEN_EXPIRY"]
            del os.environ["TEST_VALIDATION_DEBUG"]

    def test_config_validation(self):
        """Test that configuration values are validated."""
        # This should fail - validation doesn't exist
        config = ValidationConfig()

        # Valid configuration should pass
        valid_config = {
            "database_path": "/valid/path.db",
            "token_expiry_hours": 24,
            "max_validation_attempts": 5,
            "gemini_model": "gemini-2.5-flash"
        }

        assert config.validate(valid_config) is True

        # Invalid configurations should fail
        invalid_configs = [
            {"token_expiry_hours": -1},  # Negative value
            {"max_validation_attempts": 0},  # Zero attempts
            {"gemini_model": "invalid-model"},  # Unknown model
            {"database_path": ""},  # Empty path
        ]

        for invalid_config in invalid_configs:
            assert config.validate(invalid_config) is False

    def test_config_schema_enforcement(self):
        """Test that configuration follows defined schema."""
        # This should fail - schema enforcement doesn't exist
        config = ValidationConfig()

        # Get schema
        schema = config.get_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "required" in schema

        # Required fields should be defined
        required_fields = schema["required"]
        assert "database_path" in required_fields
        assert "validation_stages" in required_fields

        # Properties should have types
        properties = schema["properties"]
        assert properties["token_expiry_hours"]["type"] == "integer"
        assert properties["debug_mode"]["type"] == "boolean"
        assert properties["gemini_model"]["type"] == "string"

    def test_config_merging(self):
        """Test merging multiple configuration sources."""
        # This should fail - merging functionality doesn't exist
        base_config = ValidationConfig()

        # Load base defaults
        base_config.load_defaults()

        # Merge file config
        file_config = {
            "token_expiry_hours": 72,
            "new_setting": "from_file"
        }
        base_config.merge(file_config)

        # Merge environment config (highest priority)
        env_config = {
            "token_expiry_hours": 48,
            "debug_mode": True
        }
        base_config.merge(env_config, priority="high")

        # Check final values
        assert base_config.get("token_expiry_hours") == 48  # From env (highest priority)
        assert base_config.get("new_setting") == "from_file"  # From file
        assert base_config.get("debug_mode") is True  # From env
        assert base_config.get("max_validation_attempts") == 3  # From defaults

    def test_config_sections(self):
        """Test configuration organized in sections."""
        # This should fail - sections don't exist
        config = ValidationConfig()

        # Set values in different sections
        config.set_section("database", {
            "path": "/app/data/validation.db",
            "backup_path": "/app/backup/validation.db",
            "connection_timeout": 30
        })

        config.set_section("validation", {
            "max_attempts": 5,
            "timeout_seconds": 300,
            "required_stages": ["design", "implementation", "breaking"]
        })

        config.set_section("gemini", {
            "model": "gemini-2.5-pro",
            "api_key_env": "GEMINI_API_KEY",
            "max_tokens": 4096
        })

        # Retrieve section values
        db_config = config.get_section("database")
        assert db_config["path"] == "/app/data/validation.db"
        assert db_config["connection_timeout"] == 30

        validation_config = config.get_section("validation")
        assert validation_config["max_attempts"] == 5
        assert "breaking" in validation_config["required_stages"]

    def test_config_interpolation(self):
        """Test variable interpolation in configuration values."""
        # This should fail - interpolation doesn't exist
        config = ValidationConfig()

        # Set base variables
        config.set("app_root", "/app")
        config.set("env", "production")

        # Set values with interpolation
        config.set("database_path", "${app_root}/data/${env}/validation.db")
        config.set("log_file", "${app_root}/logs/validation-${env}.log")

        # Enable interpolation
        config.enable_interpolation()

        # Values should be interpolated
        assert config.get("database_path") == "/app/data/production/validation.db"
        assert config.get("log_file") == "/app/logs/validation-production.log"

    def test_config_type_coercion(self):
        """Test automatic type conversion for configuration values."""
        # This should fail - type coercion doesn't exist
        config = ValidationConfig()

        # Set string values that should be coerced
        config.set_raw("token_expiry_hours", "48")
        config.set_raw("debug_mode", "true")
        config.set_raw("max_attempts", "5")
        config.set_raw("rate_limit", "10.5")

        # Enable type coercion
        config.enable_type_coercion()

        # Values should be properly typed
        assert config.get("token_expiry_hours") == 48  # int
        assert config.get("debug_mode") is True  # bool
        assert config.get("max_attempts") == 5  # int
        assert config.get("rate_limit") == 10.5  # float

    def test_config_watching(self):
        """Test watching configuration files for changes."""
        # This should fail - file watching doesn't exist
        config_data = {"test_value": "original"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = ValidationConfig.load_from_file(config_path)

            # Start watching
            config.start_watching()

            assert config.get("test_value") == "original"

            # Modify file
            with open(config_path, 'w') as f:
                json.dump({"test_value": "updated"}, f)

            # Give file watcher time to detect change
            import time
            time.sleep(0.1)

            # Config should be updated
            assert config.get("test_value") == "updated"

            config.stop_watching()
        finally:
            os.unlink(config_path)

    def test_config_export(self):
        """Test exporting configuration to different formats."""
        # This should fail - export functionality doesn't exist
        config = ValidationConfig()

        # Set some configuration
        config.set("database_path", "/app/validation.db")
        config.set("debug_mode", True)
        config.set("validation_stages", ["design", "implementation"])

        # Export to JSON
        json_output = config.export_json()
        json_data = json.loads(json_output)

        assert json_data["database_path"] == "/app/validation.db"
        assert json_data["debug_mode"] is True
        assert "design" in json_data["validation_stages"]

        # Export to environment variables format
        env_output = config.export_env(prefix="TEST_VAL_")

        assert "TEST_VAL_DATABASE_PATH=/app/validation.db" in env_output
        assert "TEST_VAL_DEBUG_MODE=true" in env_output

    def test_config_profiles(self):
        """Test configuration profiles for different environments."""
        # This should fail - profiles don't exist
        config = ValidationConfig()

        # Define profiles
        config.define_profile("development", {
            "debug_mode": True,
            "database_path": ":memory:",
            "token_expiry_hours": 1,
            "gemini_model": "gemini-2.5-flash"
        })

        config.define_profile("production", {
            "debug_mode": False,
            "database_path": "/prod/data/validation.db",
            "token_expiry_hours": 168,
            "gemini_model": "gemini-2.5-pro"
        })

        # Activate development profile
        config.activate_profile("development")

        assert config.get("debug_mode") is True
        assert config.get("database_path") == ":memory:"
        assert config.get("token_expiry_hours") == 1

        # Switch to production profile
        config.activate_profile("production")

        assert config.get("debug_mode") is False
        assert config.get("database_path") == "/prod/data/validation.db"
        assert config.get("token_expiry_hours") == 168


if __name__ == "__main__":
    # Run tests - these should all FAIL in RED phase
    pytest.main([__file__, "-v"])
