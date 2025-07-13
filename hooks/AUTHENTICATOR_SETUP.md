# Google Authenticator Setup Guide for Hook Override System

This guide will walk you through setting up Google Authenticator for the Claude Code hook override system.

## Prerequisites

You'll need:
- A smartphone (iOS or Android)
- Google Authenticator app (or compatible TOTP app like Authy, Microsoft Authenticator, etc.)
- Access to your development environment

## Step-by-Step Setup

### Step 1: Install Google Authenticator

**For iPhone/iOS:**
1. Open the App Store
2. Search for "Google Authenticator"
3. Install the app by Google LLC (free)

**For Android:**
1. Open Google Play Store
2. Search for "Google Authenticator"
3. Install the app by Google LLC (free)

### Step 2: Generate Your Secret Key

On your development machine, run this command to generate a secure secret:

```bash
python3 -c "import pyotp; print(pyotp.random_base32())"
```

Example output:
```
JBSWY3DPEHPK3PXP
```

**IMPORTANT**: Save this secret securely! You'll need it for:
- Setting up Google Authenticator
- Configuring your environment
- Recovery if you lose your phone

### Step 3: Add to Google Authenticator

1. **Open Google Authenticator** on your phone

2. **Tap the "+" button** (usually in the bottom right)

3. **Select "Enter a setup key"**

4. **Enter the following:**
   - **Account name**: `Claude Hook Override`
   - **Your key**: `[The secret you generated in Step 2]`
   - **Type of key**: Select "Time based"

5. **Tap "Add"**

You should now see a 6-digit code that changes every 30 seconds!

### Step 4: Test Your Setup

Let's verify everything is working:

```bash
# First, install pyotp if you haven't already
pip install pyotp

# Test your setup with this Python script
python3 << 'EOF'
import pyotp
import time

# Replace with YOUR secret from Step 2
secret = "JBSWY3DPEHPK3PXP"
totp = pyotp.TOTP(secret)

print("Your current code should be:", totp.now())
print("This should match what you see in Google Authenticator!")
print(f"Code will change in {30 - (int(time.time()) % 30)} seconds")
EOF
```

The code shown should match what's in your Google Authenticator app!

### Step 5: Configure Your Environment

Add the secret to your environment. Choose ONE of these methods:

**Option A: Shell Profile (Permanent)**
```bash
# Add to ~/.bashrc, ~/.zshrc, or appropriate shell config
echo 'export HOOK_OVERRIDE_SECRET="JBSWY3DPEHPK3PXP"' >> ~/.bashrc
source ~/.bashrc
```

**Option B: Environment File (Project-specific)**
```bash
# Create a .env file in your project (DO NOT commit this!)
echo 'HOOK_OVERRIDE_SECRET="JBSWY3DPEHPK3PXP"' >> .env

# Add .env to .gitignore
echo '.env' >> .gitignore
```

**Option C: Secure Secret Manager (Production)**
- Use AWS Secrets Manager, HashiCorp Vault, or similar
- Consult your organization's security policies

### Step 6: Create Setup Helper Script

Create this helper script to make setup easier for your team:

```bash
cat > setup-authenticator.sh << 'EOF'
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
EOF

chmod +x setup-authenticator.sh
```

## Troubleshooting

### Codes Don't Match

If the codes don't match between your script and Google Authenticator:

1. **Check time synchronization**
   ```bash
   # Check system time
   date

   # On your phone, ensure automatic time is enabled:
   # iOS: Settings → General → Date & Time → Set Automatically
   # Android: Settings → System → Date & time → Automatic date & time
   ```

2. **Verify the secret**
   - Make sure you copied the entire secret
   - Check for spaces or typos
   - Secrets are case-sensitive

3. **Try time window tolerance**
   ```python
   # This checks current, previous, and next codes
   import pyotp
   totp = pyotp.TOTP("YOUR_SECRET")

   # Try with tolerance
   code = input("Enter code from app: ")
   if totp.verify(code, valid_window=1):
       print("✅ Code is valid!")
   else:
       print("❌ Code is invalid")
   ```

### Lost Phone / Recovery

If you lose access to your authenticator:

1. **If you saved your secret**: Simply add it to a new authenticator app
2. **If you have backup codes**: Use the recovery process
3. **If you have no backup**: You'll need to generate a new secret and reconfigure

### Multiple Devices

You can add the same secret to multiple devices:
- Use the same secret on multiple phones/tablets
- Use authenticator apps that sync (like Authy)
- Keep a backup authenticator on a secure device

## Security Best Practices

### DO:
- ✅ Save your secret in a password manager
- ✅ Use environment variables for the secret
- ✅ Enable app lock on your authenticator
- ✅ Keep your phone's OS updated
- ✅ Use automatic time synchronization

### DON'T:
- ❌ Share your secret with others
- ❌ Commit the secret to version control
- ❌ Use simple/guessable secrets
- ❌ Screenshot QR codes or secrets
- ❌ Store secrets in plain text files

## Quick Reference Card

Once set up, here's how to use it:

```bash
# When a command is blocked:
# 1. You'll see: "Ask for override code"
# 2. Open Google Authenticator
# 3. Find "Claude Hook Override"
# 4. Give the 6-digit code to the AI
# 5. AI will retry with: HOOK_OVERRIDE_CODE=123456 <command>
```

## Integration with Team

For team environments:

1. **Each developer gets their own secret**
   - More secure
   - Individual accountability
   - Can revoke access per person

2. **Or share a team secret** (less secure)
   - Easier management
   - Use secure secret sharing
   - Rotate regularly

3. **Document your choice**
   ```markdown
   # Team Override Policy
   - Method: [Individual/Shared]
   - Rotation: [Frequency]
   - Distribution: [How secrets are shared]
   ```

---

**Need help?** The setup script (`setup-authenticator.sh`) automates most of this process!
