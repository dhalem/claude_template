# Original Shell Scripts Archive

This directory contains the original shell implementations of the Claude Code hooks before migration to Python.

## Archived Files

- `adaptive-guard.sh` - Original adaptive safety guard implementation
- `lint-guard.sh` - Original linting guard implementation
- `comprehensive-guard.sh` - Original comprehensive guard implementation

## Migration Date

**Archived on**: $(date)
**Reason**: Migration to Python implementation for improved reliability, maintainability, and functionality

## Python Migration Benefits

The Python replacements provide:

1. **Bug Fixes**: Corrected Git force push logic, exit code consistency
2. **Better Error Handling**: Robust JSON parsing and graceful tool failures
3. **Enhanced Testing**: 500+ test cases with parallel validation
4. **Improved Maintainability**: Object-oriented design with comprehensive documentation
5. **Performance**: Better resource management and faster execution

## Recovery Instructions

If needed, these scripts can be restored by:

1. Copy from this archive back to the hooks directory
2. Update the install script to reference shell scripts
3. Re-run the installation

## Verification

The archived scripts can be verified with:

```bash
bash -n adaptive-guard.sh
bash -n lint-guard.sh
bash -n comprehensive-guard.sh
```
