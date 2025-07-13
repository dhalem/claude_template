# Claude Code Safety Hooks

🛡️ **Comprehensive safety hook system for Claude Code that prevents costly mistakes**

## Quick Start

```bash
# Install the hooks
cd hooks
./install-hooks.sh

# Test the installation
./test-hooks.sh
```

## What This Protects Against

These hooks prevent specific mistakes that have caused **real harm** in the past:

- 🚨 **Git bypass**: Prevents `--no-verify` without permission
- 💥 **Docker restart**: Stops catastrophic restart after code changes
- 📍 **Directory confusion**: Enforces location verification
- 🧪 **Incomplete testing**: Blocks completion claims without test evidence
- 🎭 **Mock code**: Prevents forbidden mock/simulation code
- ⚙️ **Config changes**: Guards pre-commit configuration

## Files in This Directory

| File | Purpose |
|------|---------|
| `HOOKS.md` | **Complete documentation** - read this for full details |
| `comprehensive-guard.sh` | Main safety guard script |
| `settings.json` | Hook configuration for Claude Code |
| `install-hooks.sh` | Installation script |
| `test-hooks.sh` | Testing and validation script |
| `README.md` | This quick reference |

## Installation

The installation script:

- ✅ Backs up existing Claude Code settings
- ✅ Installs guard script to `~/.claude/comprehensive-guard.sh`
- ✅ Configures hooks in `~/.claude/settings.json`
- ✅ Validates everything works correctly

## Override System

🔓 **Need to bypass a hook?** The system includes a secure override mechanism:

- Uses **Google Authenticator** for time-based codes
- Requires **explicit human approval** for each override
- Codes are **valid for 30 seconds only**
- Full **audit logging** of all overrides

**Setup**: Run `./setup-authenticator.sh` to configure Google Authenticator
**Documentation**: See `OVERRIDE_SYSTEM.md` for complete details

## For Full Documentation

👉 **Read `HOOKS.md`** for complete details on:

- How each guard works
- Adding new hooks
- Troubleshooting
- Maintenance procedures

## Why These Hooks Exist

From the project's `CLAUDE.md`:

> "On June 23, 2025, I made critical mistakes that could have been prevented by following existing rules:
>
> - I woke up the user's wife by playing audio without checking volume
> - I used `docker restart` instead of rebuild, wasting hours
> - I didn't check CLAUDE.md before acting"

These hooks prevent exactly these types of documented mistakes from happening again.

## Support

If hooks aren't working:

1. Run `./test-hooks.sh` to diagnose issues
2. Check `HOOKS.md` troubleshooting section
3. Re-run `./install-hooks.sh` if needed

**Remember**: When a hook blocks an action, it's protecting you from repeating documented mistakes that have caused real harm.
