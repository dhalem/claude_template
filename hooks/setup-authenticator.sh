#!/bin/bash
# Google Authenticator setup helper for Claude hook overrides

echo "🔐 Claude Hook Override - Google Authenticator Setup"
echo "=================================================="
echo ""

# Check if pyotp is installed
if ! python3 -c "import pyotp" 2>/dev/null; then
    echo "❌ ERROR: pyotp not found!"
    echo ""
    echo "🚨 REQUIRED STEP: Run the installation script first:"
    echo "   ./hooks/install-hooks-python-only.sh"
    echo ""
    echo "This script automatically installs all Python dependencies"
    echo "including pyotp for TOTP functionality."
    echo ""
    echo "After running the installation script, run this setup again."
    exit 1
fi

echo "✅ Found pyotp - proceeding with setup..."
echo ""

# Generate secret
echo "🔑 Generating your secret key..."
SECRET=$(python3 -c "import pyotp; print(pyotp.random_base32())")
echo ""
echo "Your secret key is: $SECRET"
echo ""
echo "⚠️  IMPORTANT: Save this secret securely! You'll need it for recovery."
echo ""

# Generate QR code URL (for manual QR code generation if needed)
QR_URL="otpauth://totp/Claude%20Hook%20Override?secret=$SECRET&issuer=ClaudeTemplate"
echo "📱 QR Code URL (for QR code generators):"
echo "$QR_URL"
echo ""

# Instructions
echo "📱 Now set up Google Authenticator:"
echo "1. Open Google Authenticator on your phone"
echo "2. Tap the '+' button"
echo "3. Select 'Enter a setup key'"
echo "4. Enter:"
echo "   Account: Claude Hook Override"
echo "   Key: $SECRET"
echo "   Type: Time based"
echo "5. Tap 'Add'"
echo ""

# Test the setup
echo "✅ Let's verify your setup..."
echo "Please enter the current 6-digit code from Google Authenticator:"
read -r user_code

# Get the current valid code
current_code=$(python3 -c "import pyotp; print(pyotp.TOTP('$SECRET').now())")

if [[ "$user_code" == "$current_code" ]]; then
    echo ""
    echo "🎉 Great! Setup verified successfully."
    echo ""

    # Automatically set up environment variable in hooks .env file
    echo "🔧 Setting up environment variable for hooks..."

    # Create .env file in Claude hooks directory
    CLAUDE_DIR="$HOME/.claude"
    ENV_FILE="$CLAUDE_DIR/.env"

    # Create or update .env file
    if [[ -f "$ENV_FILE" ]]; then
        # Check if HOOK_OVERRIDE_SECRET already exists
        if grep -q "HOOK_OVERRIDE_SECRET" "$ENV_FILE"; then
            # Update existing entry
            sed -i.backup "s/^HOOK_OVERRIDE_SECRET=.*/HOOK_OVERRIDE_SECRET=\"$SECRET\"/" "$ENV_FILE"
            echo "✅ Updated HOOK_OVERRIDE_SECRET in $ENV_FILE"
        else
            # Add new entry
            echo "" >> "$ENV_FILE"
            echo "# Claude Hook Override System" >> "$ENV_FILE"
            echo "HOOK_OVERRIDE_SECRET=\"$SECRET\"" >> "$ENV_FILE"
            echo "✅ Added HOOK_OVERRIDE_SECRET to $ENV_FILE"
        fi
    else
        # Create new .env file
        cat > "$ENV_FILE" << EOF
# Claude Hook Override System
# This file is automatically loaded by the hook scripts
HOOK_OVERRIDE_SECRET="$SECRET"
EOF
        echo "✅ Created $ENV_FILE with HOOK_OVERRIDE_SECRET"
    fi

    # Also set for current session for testing
    export HOOK_OVERRIDE_SECRET="$SECRET"

    echo ""
    echo "🎯 Testing override system..."

    # Test the override system with a simple command
    echo "Testing override with current environment..."
    echo '{"tool_name": "Bash", "tool_input": {"command": "echo test"}}' | HOOK_OVERRIDE_CODE=$(python3 -c "import pyotp; print(pyotp.TOTP('$SECRET').now())") python3 ~/.claude/python/main.py adaptive >/dev/null 2>&1

    if [[ $? -eq 0 ]]; then
        echo "✅ Override system test passed!"
    else
        echo "⚠️  Override system test had issues (this may be normal if no guards triggered)"
    fi

    echo ""
    echo "🎉 Setup complete! Your override system is ready to use."
    echo ""
    echo "📋 How to use:"
    echo "• When hooks block commands, you'll see override instructions"
    echo "• Get 6-digit code from Google Authenticator"
    echo "• Re-run with: HOOK_OVERRIDE_CODE=123456 your-command"
else
    echo ""
    echo "❌ The code doesn't match. Please check:"
    echo "1. You entered the secret correctly in Google Authenticator"
    echo "2. Your phone's time is synchronized"
    echo "3. You selected 'Time based' in the app"
    echo "4. You entered the code exactly as shown (6 digits)"
    echo ""
    echo "You entered: $user_code"
    echo "Expected: $current_code"
    echo ""
    echo "Please try running the setup again or wait for the next code cycle."
fi
