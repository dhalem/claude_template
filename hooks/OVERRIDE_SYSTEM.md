# Hook Override System Documentation

## Overview

The Claude Code hook system includes a secure bypass mechanism that allows authorized users to override safety guards when necessary. This system uses Time-based One-Time Passwords (TOTP) via Google Authenticator to ensure that overrides are:

- **Time-limited** (30-second validity window)
- **Explicitly authorized** by the human operator
- **Auditable** with full logging
- **Non-reusable** (each code works only once)

## How It Works

### 1. Command Gets Blocked

When a hook blocks a potentially dangerous command, you'll see an error message like:

```
🚨 COMMAND BLOCKED: Dangerous pattern detected
Reason: Attempting to delete system files
Suggestion: Use a more specific path or safer command

🔓 To override this block with explicit approval:
   1. Ask the human operator for an override code
   2. Re-run with: HOOK_OVERRIDE_CODE=<code> <your command>

⚠️  Override codes are time-limited and require human authorization.
```

### 2. Request Override Code

The AI assistant should request an override code from the human operator:

```
"This command was blocked by safety hooks. May I have an override code to proceed with your explicit approval?"
```

### 3. Human Provides TOTP Code

The human operator:
1. Opens Google Authenticator app
2. Finds the "Claude Hook Override" entry
3. Provides the current 6-digit code (e.g., `847293`)

### 4. AI Uses Override Code

The AI re-runs the command with the override code:

```bash
HOOK_OVERRIDE_CODE=847293 rm -rf /important/directory
```

### 5. Hook Validates Code

The hook system:
1. Extracts the override code from environment variable
2. Validates it against the TOTP secret
3. Checks that the code hasn't been used recently
4. If valid, allows the command to proceed
5. Logs the override event for audit purposes

## Security Architecture

### TOTP Implementation

```python
# Validation flow in base_guard.py
def check_override(self, command_data):
    """Check if a valid override code is provided."""
    override_code = os.environ.get('HOOK_OVERRIDE_CODE')

    if not override_code:
        return False

    # Validate TOTP code
    if self.validate_totp(override_code):
        self.log_override(command_data, override_code)
        return True

    return False

def validate_totp(self, code):
    """Validate TOTP code using pyotp."""
    import pyotp

    # Secret is stored securely (environment variable or secure config)
    totp_secret = self.get_totp_secret()
    totp = pyotp.TOTP(totp_secret)

    # Check current and previous window (allows for clock skew)
    return totp.verify(code, valid_window=1)
```

### Audit Logging

All override attempts are logged with:
- Timestamp
- Command that was overridden
- Guard that was bypassed
- Success/failure of override attempt
- User context (if available)

```json
{
  "timestamp": "2024-01-13T10:30:45Z",
  "event": "hook_override",
  "guard": "file_deletion_guard",
  "command": "rm -rf /important/directory",
  "override_successful": true,
  "code_used": "847293",
  "context": {
    "working_directory": "/home/user/project",
    "tool": "bash"
  }
}
```

## Setup Instructions

**🚨 IMPORTANT: The installation script automatically handles all Python dependencies and requirements setup for the venv it uses. You don't need to manually install anything.**

**📱 For complete step-by-step setup including Google Authenticator installation and configuration, see [AUTHENTICATOR_SETUP.md](AUTHENTICATOR_SETUP.md)**

### Quick Setup (Recommended)

1. **Install the hook system with override functionality**:
   ```bash
   ./hooks/install-hooks-python-only.sh
   ```
   This installation script automatically:
   - ✅ Installs all Python dependencies (including pyotp)
   - ✅ Sets up the hook system with override functionality
   - ✅ Configures the proper Python environment
   - ✅ Updates hook wrapper scripts
   - ✅ Provides clear next steps

2. **Install Google Authenticator** on your phone (iOS/Android)

3. **Run the automated setup script**:
   ```bash
   ./hooks/setup-authenticator.sh
   ```
   This will:
   - Generate a secure secret
   - Guide you through adding it to Google Authenticator
   - Verify your setup is working
   - **Automatically create .env file in hooks directory**
   - **Ready to use immediately - hooks load the secret automatically**

### Manual Setup

If you prefer manual setup:

```bash
# 1. Generate TOTP Secret
python -c "import pyotp; print(pyotp.random_base32())"
# Example output: JBSWY3DPEHPK3PXP

# 2. Add to Google Authenticator app:
#    - Tap "+" → "Enter a setup key"
#    - Account: Claude Hook Override
#    - Key: [Your generated secret]
#    - Type: Time based

# 3. Configure environment
export HOOK_OVERRIDE_SECRET="JBSWY3DPEHPK3PXP"

# 4. Test the system
echo '{"tool": "bash", "command": "rm -rf /"}' | ./hooks/adaptive-guard.sh
```

## Usage Guidelines

### For Human Operators

1. **Only provide override codes when you fully understand the command**
2. **Each code is valid for only 30 seconds**
3. **Never share your TOTP secret**
4. **Review audit logs regularly**
5. **Consider the security implications before overriding**

### For AI Assistants

1. **Always show the full blocked command to the user**
2. **Explain why the command was blocked**
3. **Request an override code only when necessary**
4. **Include the override code in the environment variable**
5. **Never store or reuse override codes**

### Example Interaction

```
AI: I need to delete the old backup directory, but the command was blocked:

🚨 COMMAND BLOCKED: Attempting to delete directory with rm -rf
Command: rm -rf /backups/old_2023

This was blocked because rm -rf can be dangerous. May I have an override code to proceed with your explicit approval?
```

Human: Sure, here is the code from my authenticator: 847293

AI: Thank you. I will retry with the override code:

```bash
HOOK_OVERRIDE_CODE=847293 rm -rf /backups/old_2023
```

[Command proceeds if code is valid]

## Error Handling

### Invalid Override Codes

If an invalid override code is provided, the system:
1. **Does NOT throw an error**
2. **Continues with normal blocking behavior**
3. **Logs the failed override attempt**
4. **Shows the standard block message again**

This ensures that:
- Invalid codes do not create confusing error states
- The safety system remains active
- Users understand the command is still blocked
- There is no way to "break" the system with bad codes

### Example with Invalid Code

```bash
# User provides wrong/expired code
HOOK_OVERRIDE_CODE=000000 rm -rf /important/directory

# Hook response (same as without override):
🚨 COMMAND BLOCKED: Dangerous pattern detected
Reason: Attempting to delete system files
Suggestion: Use a more specific path or safer command

🔓 To override this block with explicit approval:
   1. Ask the human operator for an override code
   2. Re-run with: HOOK_OVERRIDE_CODE=<code> <your command>
```

## Implementation Details

### Required Dependencies

```python
# Add to requirements.txt or requirements-dev.txt
pyotp>=2.9.0  # For TOTP validation
```

### Environment Variables

- `HOOK_OVERRIDE_SECRET` - The base32 TOTP secret (set by admin)
- `HOOK_OVERRIDE_CODE` - The 6-digit code (set per command)
- `HOOK_OVERRIDE_LOG_PATH` - Optional: Custom log file path

### Security Considerations

1. **Secret Storage**
   - Never commit the TOTP secret to version control
   - Store in secure environment variables or secret management
   - Rotate periodically for enhanced security

2. **Rate Limiting**
   - Implement rate limiting on override attempts
   - Block after N failed attempts within time window
   - Log all attempts for security monitoring

3. **Audit Trail**
   - All overrides are logged with full context
   - Logs should be immutable and monitored
   - Consider sending to SIEM for analysis

## Testing the Override System

### Unit Tests

```python
def test_valid_override_allows_command():
    """Test that valid TOTP code allows command."""
    guard = FileGuard()
    os.environ["HOOK_OVERRIDE_CODE"] = generate_valid_totp()

    result = guard.check({"command": "rm -rf /"})
    assert result["blocked"] is False
    assert "override_used" in result

def test_invalid_override_maintains_block():
    """Test that invalid code does not bypass block."""
    guard = FileGuard()
    os.environ["HOOK_OVERRIDE_CODE"] = "000000"

    result = guard.check({"command": "rm -rf /"})
    assert result["blocked"] is True
    assert "override_failed" in result.get("metadata", {})
```

### Integration Tests

```bash
# Test with valid code
HOOK_OVERRIDE_SECRET="JBSWY3DPEHPK3PXP" \
HOOK_OVERRIDE_CODE=$(oathtool --totp -b JBSWY3DPEHPK3PXP) \
echo '{"command": "rm -rf /"}'  < /dev/null |  ./hooks/adaptive-guard.sh

# Test with invalid code
HOOK_OVERRIDE_CODE="000000" \
echo '{"command": "rm -rf /"}' | ./hooks/adaptive-guard.sh
```

## Monitoring and Alerting

### Metrics to Track

- Override attempts (successful/failed)
- Commands that triggered override requests
- Time between override attempts
- Unique override codes used

### Alert Conditions

- Multiple failed override attempts
- Unusual pattern of override usage
- Override used for highly dangerous commands
- Override attempts outside business hours

---

**Important**: This override system is designed to maintain safety while providing flexibility. It should only be used when absolutely necessary and with full understanding of the risks involved.
