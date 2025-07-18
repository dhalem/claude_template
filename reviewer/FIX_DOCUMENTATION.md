# Code Review MCP Server - Capabilities Fix Documentation

## Problem
The code-review MCP server was showing "Capabilities: none" when connected, meaning it couldn't expose any tools.

## Root Cause
The server script used `__file__` to determine its location for importing required modules. However, when the server is launched in certain contexts (like through the MCP protocol), `__file__` may not be defined, causing a NameError during initialization.

## Solution
Fixed the path resolution to handle cases where `__file__` is not defined:

```python
# Handle case where __file__ might not be defined
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # If __file__ is not defined, try to use sys.argv[0] or fallback
    if sys.argv and sys.argv[0]:
        current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # Last resort: assume we're in the correct directory
        current_dir = os.path.abspath(".")
```

## Testing Process
1. Created test script to identify the exact error
2. Confirmed all imports work when paths are correct
3. Identified `__file__` NameError as the issue
4. Applied fix to handle missing `__file__`
5. Reinstalled server with the fix

## Key Learning
When writing MCP servers, avoid relying on `__file__` for path resolution as it may not be available in all execution contexts. Always provide fallback mechanisms for determining the script's location.

## Status
The fix has been applied and the server reinstalled. The code-review server should now properly expose its `review_code` tool instead of showing "Capabilities: none".
