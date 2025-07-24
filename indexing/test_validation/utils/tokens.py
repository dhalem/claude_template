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
Validation token generation and management for test validation system.
Provides secure token generation, validation, and lifecycle management.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class ValidationTokenManager:
    """Manages validation tokens for the test validation system."""

    def __init__(self,
                 secret_key: Optional[str] = None,
                 default_expiry_hours: int = 168,
                 storage_path: Optional[str] = None,
                 rate_limit_per_minute: int = 60):
        """Initialize the token manager.

        Args:
            secret_key: Secret key for token signing (generates random if None)
            default_expiry_hours: Default token expiry time in hours (7 days)
            storage_path: Path for persistent token storage
            rate_limit_per_minute: Maximum tokens generated per minute
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.default_expiry_hours = default_expiry_hours
        self.storage_path = storage_path
        self.rate_limit_per_minute = rate_limit_per_minute

        # In-memory storage for tokens
        self._tokens: Dict[str, Dict[str, Any]] = {}
        self._usage_info: Dict[str, Dict[str, Any]] = {}
        self._revoked_tokens: set = set()

        # Rate limiting
        self._rate_limit_tracker: Dict[str, List[float]] = {}

        # Initialize persistent storage if specified
        if self.storage_path:
            self._init_storage()

    def _init_storage(self):
        """Initialize persistent token storage."""
        if not self.storage_path:
            return

        # Create storage directory if needed
        storage_dir = Path(self.storage_path).parent
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite database for token storage
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()

        # Create tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                token TEXT PRIMARY KEY,
                fingerprint TEXT NOT NULL,
                stage TEXT NOT NULL,
                issued_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                metadata TEXT,
                revoked INTEGER DEFAULT 0
            )
        ''')

        # Create usage table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS token_usage (
                token TEXT PRIMARY KEY,
                used_at TEXT,
                action TEXT,
                user TEXT,
                FOREIGN KEY (token) REFERENCES tokens (token)
            )
        ''')

        conn.commit()
        conn.close()

    def generate_token(self,
                      fingerprint: str,
                      stage: str,
                      expires_in_hours: Optional[int] = None,
                      metadata: Optional[Dict[str, Any]] = None,
                      user_id: Optional[str] = None) -> str:
        """Generate a validation token.

        Args:
            fingerprint: Test fingerprint
            stage: Validation stage
            expires_in_hours: Custom expiry time (uses default if None)
            metadata: Additional token metadata
            user_id: User identifier for rate limiting (optional)

        Returns:
            Secure validation token string

        Raises:
            Exception: If rate limit exceeded
        """
        # Check rate limit per user
        self._check_rate_limit(user_id or "default")

        # Set expiry time
        expiry_hours = expires_in_hours or self.default_expiry_hours
        issued_at = datetime.now()
        expires_at = issued_at + timedelta(hours=expiry_hours)

        # Create token payload
        payload = {
            'fingerprint': fingerprint,
            'stage': stage,
            'issued_at': issued_at.isoformat(),
            'expires_at': expires_at.isoformat(),
            'metadata': metadata or {},
            'nonce': secrets.token_hex(16)  # Ensure uniqueness
        }

        # Encode payload
        payload_json = json.dumps(payload, sort_keys=True)
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()

        # Generate signature
        signature = self._sign_payload(payload_b64)

        # Combine payload and signature
        token_raw = f"{payload_b64}.{signature}"

        # Encode entire token to ensure only safe characters (alphanumeric, hyphens, underscores)
        token = base64.urlsafe_b64encode(token_raw.encode()).decode().rstrip('=')

        # Store token (use raw token as key for internal operations)
        self._tokens[token] = payload

        # Store in persistent storage
        if self.storage_path:
            self._store_token_persistent(token, payload)

        return token

    def _check_rate_limit(self, user_id: str = "default"):
        """Check if rate limit is exceeded for a specific user.

        Args:
            user_id: User identifier for rate limiting (defaults to "default" for backward compatibility)
        """
        now = time.time()
        minute_ago = now - 60

        # Get current minute's requests for this user
        if user_id not in self._rate_limit_tracker:
            self._rate_limit_tracker[user_id] = []

        # Remove old entries
        self._rate_limit_tracker[user_id] = [
            timestamp for timestamp in self._rate_limit_tracker[user_id]
            if timestamp > minute_ago
        ]

        # Check limit
        if len(self._rate_limit_tracker[user_id]) >= self.rate_limit_per_minute:
            raise Exception(f"Rate limit exceeded for user '{user_id}'. Too many tokens generated per minute.")

        # Add current request
        self._rate_limit_tracker[user_id].append(now)

    def _sign_payload(self, payload: str) -> str:
        """Sign payload with secret key."""
        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _store_token_persistent(self, token: str, payload: Dict[str, Any]):
        """Store token in persistent storage."""
        if not self.storage_path:
            return

        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO tokens
            (token, fingerprint, stage, issued_at, expires_at, metadata, revoked)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            token,
            payload['fingerprint'],
            payload['stage'],
            payload['issued_at'],
            payload['expires_at'],
            json.dumps(payload.get('metadata', {})),
            0
        ))

        conn.commit()
        conn.close()

    def validate_token(self, token: str, fingerprint: str, stage: str) -> bool:
        """Validate a token against fingerprint and stage.

        Args:
            token: Token to validate
            fingerprint: Expected test fingerprint
            stage: Expected validation stage

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Check if token is revoked
            if self.is_revoked(token):
                return False

            # Check if token is used
            if self._is_token_used(token):
                return False

            # Verify signature
            if not self.verify_signature(token):
                return False

            # Decode token
            decoded = self.decode_token(token)
            if not decoded:
                return False

            # Check expiration
            if self.is_expired(token):
                return False

            # Check fingerprint and stage
            if decoded['fingerprint'] != fingerprint:
                return False

            if decoded['stage'] != stage:
                return False

            return True

        except Exception:
            return False

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode token payload.

        Args:
            token: Token to decode

        Returns:
            Decoded payload or None if invalid
        """
        try:
            # First decode the base64-encoded token back to raw format
            token_raw = base64.urlsafe_b64decode(token.encode() + b'==').decode()

            # Split token into payload and signature
            parts = token_raw.split('.')
            if len(parts) != 2:
                return None

            payload_b64, signature = parts

            # Decode payload
            payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
            payload = json.loads(payload_json)

            return payload

        except Exception:
            return None

    def verify_signature(self, token: str) -> bool:
        """Verify token signature.

        Args:
            token: Token to verify

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # First decode the base64-encoded token back to raw format
            token_raw = base64.urlsafe_b64decode(token.encode() + b'==').decode()

            # Split token
            parts = token_raw.split('.')
            if len(parts) != 2:
                return False

            payload_b64, provided_signature = parts

            # Generate expected signature
            expected_signature = self._sign_payload(payload_b64)

            # Compare signatures securely
            return hmac.compare_digest(expected_signature, provided_signature)

        except Exception:
            return False

    def is_expired(self, token: str) -> bool:
        """Check if token is expired.

        Args:
            token: Token to check

        Returns:
            True if expired, False otherwise
        """
        try:
            decoded = self.decode_token(token)
            if not decoded:
                return True

            expires_at = datetime.fromisoformat(decoded['expires_at'])
            return datetime.now() > expires_at

        except Exception:
            return True

    def get_expiry_time(self, token: str) -> Optional[datetime]:
        """Get token expiry time.

        Args:
            token: Token to check

        Returns:
            Expiry datetime or None if invalid
        """
        try:
            decoded = self.decode_token(token)
            if not decoded:
                return None

            return datetime.fromisoformat(decoded['expires_at'])

        except Exception:
            return None

    def revoke_token(self, token: str):
        """Revoke a token.

        Args:
            token: Token to revoke
        """
        self._revoked_tokens.add(token)

        # Update persistent storage
        if self.storage_path:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE tokens SET revoked = 1 WHERE token = ?', (token,))
            conn.commit()
            conn.close()

    def is_revoked(self, token: str) -> bool:
        """Check if token is revoked.

        Args:
            token: Token to check

        Returns:
            True if revoked, False otherwise
        """
        if token in self._revoked_tokens:
            return True

        # Check persistent storage
        if self.storage_path:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            cursor.execute('SELECT revoked FROM tokens WHERE token = ?', (token,))
            result = cursor.fetchone()
            conn.close()

            if result and result[0] == 1:
                self._revoked_tokens.add(token)  # Cache for performance
                return True

        return False

    def mark_used(self, token: str, action: str, user: str):
        """Mark token as used.

        Args:
            token: Token to mark as used
            action: Action performed with token
            user: User who used the token
        """
        usage_info = {
            'used': True,
            'action': action,
            'user': user,
            'used_at': datetime.now().isoformat()
        }

        self._usage_info[token] = usage_info

        # Store in persistent storage
        if self.storage_path:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO token_usage (token, used_at, action, user)
                VALUES (?, ?, ?, ?)
            ''', (token, usage_info['used_at'], action, user))
            conn.commit()
            conn.close()

    def get_usage_info(self, token: str) -> Dict[str, Any]:
        """Get token usage information.

        Args:
            token: Token to check

        Returns:
            Usage information dictionary
        """
        # Check in-memory storage first
        if token in self._usage_info:
            return self._usage_info[token].copy()

        # Check persistent storage
        if self.storage_path:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT used_at, action, user FROM token_usage WHERE token = ?
            ''', (token,))
            result = cursor.fetchone()
            conn.close()

            if result:
                usage_info = {
                    'used': True,
                    'used_at': result[0],
                    'action': result[1],
                    'user': result[2]
                }
                self._usage_info[token] = usage_info  # Cache for performance
                return usage_info.copy()

        # Default: not used
        return {'used': False}

    def _is_token_used(self, token: str) -> bool:
        """Check if token has been used."""
        usage_info = self.get_usage_info(token)
        return usage_info.get('used', False)

    def generate_batch(self, fingerprints: List[str], stage: str) -> List[str]:
        """Generate multiple tokens efficiently.

        Args:
            fingerprints: List of test fingerprints
            stage: Validation stage for all tokens

        Returns:
            List of generated tokens
        """
        tokens = []
        for fingerprint in fingerprints:
            token = self.generate_token(fingerprint, stage)
            tokens.append(token)
        return tokens

    def validate_batch(self, tokens: List[str], fingerprints: List[str], stages: List[str]) -> List[bool]:
        """Validate multiple tokens efficiently.

        Args:
            tokens: List of tokens to validate
            fingerprints: List of expected fingerprints
            stages: List of expected stages

        Returns:
            List of validation results
        """
        results = []
        for token, fingerprint, stage in zip(tokens, fingerprints, stages):
            is_valid = self.validate_token(token, fingerprint, stage)
            results.append(is_valid)
        return results

    def revoke_batch(self, tokens: List[str]):
        """Revoke multiple tokens efficiently.

        Args:
            tokens: List of tokens to revoke
        """
        for token in tokens:
            self.revoke_token(token)

    def cleanup_expired(self) -> int:
        """Clean up expired tokens.

        Returns:
            Number of tokens cleaned up
        """
        cleaned_count = 0

        # Clean up in-memory storage
        expired_tokens = []
        for token in list(self._tokens.keys()):
            if self.is_expired(token):
                expired_tokens.append(token)

        for token in expired_tokens:
            del self._tokens[token]
            if token in self._usage_info:
                del self._usage_info[token]
            cleaned_count += 1

        # Clean up persistent storage
        if self.storage_path:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()

            # Delete expired tokens
            now = datetime.now().isoformat()
            cursor.execute('DELETE FROM tokens WHERE expires_at < ?', (now,))
            cleaned_count += cursor.rowcount

            conn.commit()
            conn.close()

        return cleaned_count

    def analyze_security(self, token: str) -> Dict[str, Any]:
        """Analyze token security properties.

        Args:
            token: Token to analyze

        Returns:
            Security analysis results
        """
        try:
            # Basic analysis
            analysis = {
                'entropy_bits': self._calculate_entropy(token),
                'character_diversity': self._calculate_character_diversity(token),
                'has_timestamp': False,
                'has_signature': self.verify_signature(token)
            }

            # Check for timestamp
            decoded = self.decode_token(token)
            if decoded and 'issued_at' in decoded:
                analysis['has_timestamp'] = True

            return analysis

        except Exception:
            return {
                'entropy_bits': 0,
                'character_diversity': 0.0,
                'has_timestamp': False,
                'has_signature': False
            }

    def _calculate_entropy(self, token: str) -> float:
        """Calculate token entropy in bits."""
        # Simplified entropy calculation
        # In practice, would use more sophisticated analysis
        unique_chars = len(set(token))
        length = len(token)

        if length == 0:
            return 0

        # Rough entropy estimate
        import math
        entropy_per_char = math.log2(unique_chars) if unique_chars > 1 else 0
        return entropy_per_char * length

    def _calculate_character_diversity(self, token: str) -> float:
        """Calculate character diversity ratio."""
        if not token:
            return 0.0

        # Count different character types
        has_lower = any(c.islower() for c in token)
        has_upper = any(c.isupper() for c in token)
        has_digit = any(c.isdigit() for c in token)
        has_special = any(not c.isalnum() for c in token)

        char_types = sum([has_lower, has_upper, has_digit, has_special])
        return char_types / 4.0  # Normalize to 0-1

    def _cleanup_storage(self):
        """Clean up storage (for testing)."""
        if self.storage_path and os.path.exists(self.storage_path):
            os.unlink(self.storage_path)
