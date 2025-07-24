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
Configuration management for Test Validation MCP system.
Provides centralized configuration loading, validation, and management.
"""

import json
import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ConfigWatcher(FileSystemEventHandler):
    """File system event handler for configuration file watching."""

    def __init__(self, config_instance, config_path: str):
        self.config_instance = config_instance
        self.config_path = Path(config_path).resolve()

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and Path(event.src_path).resolve() == self.config_path:
            self.config_instance._reload_from_file()


class ValidationConfig:
    """Manages configuration for the test validation system."""

    # Configuration schema for validation
    _SCHEMA = {
        "type": "object",
        "properties": {
            "database_path": {"type": "string", "minLength": 1},
            "token_expiry_hours": {"type": "integer", "minimum": 1},
            "max_validation_attempts": {"type": "integer", "minimum": 1},
            "gemini_model": {"type": "string", "enum": ["gemini-2.5-flash", "gemini-2.5-pro"]},
            "validation_stages": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1
            },
            "debug_mode": {"type": "boolean"},
            "rate_limit_per_minute": {"type": "integer", "minimum": 1}
        },
        "required": ["database_path", "validation_stages"]
    }

    # Default configuration values
    _DEFAULTS = {
        "database_path": "./data/test_validation.db",
        "token_expiry_hours": 168,  # 7 days
        "max_validation_attempts": 3,
        "gemini_model": "gemini-2.5-flash",
        "validation_stages": ["design", "implementation", "breaking", "approval"],
        "debug_mode": False,
        "rate_limit_per_minute": 60,
        "database": {
            "path": "./data/test_validation.db",
            "backup_path": "./data/backup/test_validation.db",
            "connection_timeout": 30
        },
        "validation": {
            "max_attempts": 3,
            "timeout_seconds": 300,
            "required_stages": ["design", "implementation", "breaking"]
        },
        "gemini": {
            "model": "gemini-2.5-flash",
            "api_key_env": "GEMINI_API_KEY",
            "max_tokens": 4096
        }
    }

    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize configuration manager.

        Args:
            config_data: Initial configuration data
        """
        self._config: Dict[str, Any] = {}
        self._profiles: Dict[str, Dict[str, Any]] = {}
        self._active_profile: Optional[str] = None
        self._interpolation_enabled = False
        self._type_coercion_enabled = False
        self._watcher = None
        self._observer = None
        self._file_path: Optional[str] = None
        self._lock = threading.RLock()

        if config_data:
            self._config = config_data.copy()
        else:
            self.load_defaults()

    @classmethod
    def load_from_file(cls, file_path: str) -> 'ValidationConfig':
        """Load configuration from JSON file.

        Args:
            file_path: Path to configuration file

        Returns:
            ValidationConfig instance with loaded data
        """
        with open(file_path, 'r') as f:
            config_data = json.load(f)

        instance = cls(config_data)
        instance._file_path = file_path
        return instance

    def load_defaults(self):
        """Load default configuration values."""
        with self._lock:
            self._config = self._DEFAULTS.copy()

    def get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values.

        Returns:
            Dictionary of default configuration values
        """
        return self._DEFAULTS.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        with self._lock:
            value = self._config.get(key, default)

            if self._interpolation_enabled and isinstance(value, str):
                return self._interpolate_value(value)

            if self._type_coercion_enabled:
                return self._coerce_type(key, value)

            return value

    def set(self, key: str, value: Any):
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        with self._lock:
            self._config[key] = value

    def set_raw(self, key: str, value: str):
        """Set raw string configuration value (for type coercion testing).

        Args:
            key: Configuration key
            value: Raw string value
        """
        with self._lock:
            self._config[key] = value

    def load_with_env_overrides(self, prefix: str = ""):
        """Load configuration with environment variable overrides.

        Args:
            prefix: Environment variable prefix
        """
        with self._lock:
            for env_key, env_value in os.environ.items():
                if env_key.startswith(prefix):
                    config_key = env_key[len(prefix):].lower().replace('_', '_')

                    # Convert environment key to config key
                    if config_key == "db_path":
                        config_key = "database_path"
                    elif config_key == "token_expiry":
                        config_key = "token_expiry_hours"
                    elif config_key == "debug":
                        config_key = "debug_mode"

                    # Convert value types
                    if env_value.lower() in ("true", "false"):
                        self._config[config_key] = env_value.lower() == "true"
                    elif env_value.isdigit():
                        self._config[config_key] = int(env_value)
                    else:
                        self._config[config_key] = env_value

    def validate(self, config_data: Dict[str, Any]) -> bool:
        """Validate configuration data against schema.

        Args:
            config_data: Configuration data to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation logic
        for key, value in config_data.items():
            if key == "token_expiry_hours" and (not isinstance(value, int) or value < 1) or key == "max_validation_attempts" and (not isinstance(value, int) or value < 1) or key == "gemini_model" and value not in ["gemini-2.5-flash", "gemini-2.5-pro"] or key == "database_path" and (not isinstance(value, str) or not value.strip()):
                return False

        return True

    def get_schema(self) -> Dict[str, Any]:
        """Get configuration schema.

        Returns:
            Configuration schema dictionary
        """
        return self._SCHEMA.copy()

    def merge(self, other_config: Dict[str, Any], priority: str = "normal"):
        """Merge configuration from another source.

        Args:
            other_config: Configuration data to merge
            priority: Merge priority ("normal" or "high")
        """
        with self._lock:
            if priority == "high":
                # High priority overwrites existing values
                self._config.update(other_config)
            else:
                # Normal priority only sets missing values
                for key, value in other_config.items():
                    if key not in self._config:
                        self._config[key] = value

    def set_section(self, section_name: str, section_data: Dict[str, Any]):
        """Set configuration section.

        Args:
            section_name: Name of the configuration section
            section_data: Section configuration data
        """
        with self._lock:
            self._config[section_name] = section_data

    def get_section(self, section_name: str) -> Dict[str, Any]:
        """Get configuration section.

        Args:
            section_name: Name of the configuration section

        Returns:
            Section configuration data
        """
        with self._lock:
            return self._config.get(section_name, {}).copy()

    def enable_interpolation(self):
        """Enable variable interpolation in configuration values."""
        self._interpolation_enabled = True

    def _interpolate_value(self, value: str) -> str:
        """Interpolate variables in configuration value.

        Args:
            value: String value with potential variables

        Returns:
            Interpolated string value
        """
        # Simple variable interpolation: ${variable_name}
        pattern = r'\$\{([^}]+)\}'

        def replace_var(match):
            var_name = match.group(1)
            return str(self._config.get(var_name, match.group(0)))

        return re.sub(pattern, replace_var, value)

    def enable_type_coercion(self):
        """Enable automatic type conversion for configuration values."""
        self._type_coercion_enabled = True

    def _coerce_type(self, key: str, value: Any) -> Any:
        """Coerce value to appropriate type.

        Args:
            key: Configuration key
            value: Value to coerce

        Returns:
            Type-coerced value
        """
        if not isinstance(value, str):
            return value

        # Type coercion based on key patterns and value content
        # Check for float values first (before int check)
        if "." in value and value.replace(".", "").isdigit():
            try:
                return float(value)
            except ValueError:
                pass
        elif "hours" in key or "attempts" in key or ("limit" in key and "." not in value):
            try:
                return int(value)
            except ValueError:
                pass
        elif "mode" in key and value.lower() in ("true", "false"):
            return value.lower() == "true"

        return value

    def start_watching(self):
        """Start watching configuration file for changes."""
        if not self._file_path or self._observer:
            return

        self._watcher = ConfigWatcher(self, self._file_path)
        self._observer = Observer()
        self._observer.schedule(
            self._watcher,
            str(Path(self._file_path).parent),
            recursive=False
        )
        self._observer.start()

    def stop_watching(self):
        """Stop watching configuration file for changes."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            self._watcher = None

    def _reload_from_file(self):
        """Reload configuration from file."""
        if not self._file_path:
            return

        try:
            with open(self._file_path, 'r') as f:
                new_config = json.load(f)

            # Validate new configuration before applying
            if not self.validate(new_config):
                print(f"Warning: Invalid configuration in {self._file_path}, skipping reload")
                return

            with self._lock:
                self._config.update(new_config)
        except FileNotFoundError:
            print(f"Warning: Configuration file {self._file_path} not found during reload")
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {self._file_path}: {e}")
        except Exception as e:
            print(f"Warning: Failed to reload configuration from {self._file_path}: {e}")

    def export_json(self) -> str:
        """Export configuration as JSON string.

        Returns:
            JSON string representation of configuration
        """
        with self._lock:
            return json.dumps(self._config, indent=2)

    def export_env(self, prefix: str = "") -> str:
        """Export configuration as environment variables format.

        Args:
            prefix: Prefix for environment variable names

        Returns:
            Environment variables format string
        """
        with self._lock:
            lines = []
            for key, value in self._config.items():
                if isinstance(value, dict):
                    continue  # Skip nested dictionaries

                env_key = f"{prefix}{key.upper()}"
                if isinstance(value, bool):
                    env_value = "true" if value else "false"
                else:
                    env_value = str(value)

                lines.append(f"{env_key}={env_value}")

            return "\n".join(lines)

    def define_profile(self, profile_name: str, profile_config: Dict[str, Any]):
        """Define a configuration profile.

        Args:
            profile_name: Name of the profile
            profile_config: Configuration data for the profile
        """
        with self._lock:
            self._profiles[profile_name] = profile_config.copy()

    def activate_profile(self, profile_name: str):
        """Activate a configuration profile.

        Args:
            profile_name: Name of the profile to activate
        """
        with self._lock:
            if profile_name in self._profiles:
                self._config.update(self._profiles[profile_name])
                self._active_profile = profile_name

    def __del__(self):
        """Cleanup resources on deletion."""
        self.stop_watching()
