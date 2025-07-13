#!/bin/bash
# Google Authenticator setup helper for Claude hook overrides

echo "🔐 Claude Hook Override - Google Authenticator Setup"
echo "=================================================="
echo ""

# Check if pyotp is installed
if ! python3 -c "import pyotp" 2>/dev/null; then
    echo "📦 Installing pyotp..."
    pip install pyotp
fi

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
echo "The current code should be: $(python3 -c "import pyotp; print(pyotp.TOTP('$SECRET').now())")"
echo "Does this match what you see in Google Authenticator? (y/n)"
read -r response

if [[ "$response" == "y" ]]; then
    echo ""
    echo "🎉 Great! Setup verified successfully."
    echo ""
    echo "📝 Now add this to your environment:"
    echo "   export HOOK_OVERRIDE_SECRET=\"$SECRET\""
    echo ""
    echo "You can add it to:"
    echo "- ~/.bashrc or ~/.zshrc (permanent)"
    echo "- .env file (project-specific)"
    echo "- Your secure secret manager"
else
    echo ""
    echo "❌ The codes don't match. Please check:"
    echo "1. You entered the secret correctly"
    echo "2. Your phone's time is synchronized"
    echo "3. You selected 'Time based' in the app"
fi
