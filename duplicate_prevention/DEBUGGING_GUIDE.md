# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Duplicate Prevention System - Debugging Guide

## Quick Troubleshooting Checklist

1. **Is the system blocking legitimate edits?**
   - Check if you're editing the same file (self-similarity)
   - Verify path handling is working correctly
   - Check similarity threshold settings

2. **Are Docker paths showing in error messages?**
   - Verify indexer is storing relative paths
   - Check guard path translation logic
   - Ensure workspace detection is correct

3. **Is the indexer not finding files?**
   - Check Docker volume mounts
   - Verify workspace path environment variable
   - Check file extension filters

4. **Database connection issues?**
   - Verify Qdrant is running
   - Check Docker networking
   - Validate environment variables

## Common Issues and Solutions

### Issue 1: "Similar code already exists" when editing the same file

**Symptoms**:
- Can't edit existing files
- Guard blocks changes to the file you're working on

**Root Cause**:
Self-similarity detection not working properly

**Solution**:
1. Check if the guard has the latest path comparison logic:
```bash
grep -A 10 "Skip if this is the same file" ~/.claude/python/guards/duplicate_prevention_guard.py
```

2. Verify the fix is in place:
```python
# Should see path comparison logic like:
if result_file_path == file_path:
    continue
```

3. Re-install hooks if needed:
```bash
./safe_install.sh
```

### Issue 2: Docker paths (/app/) in error messages

**Symptoms**:
- Error messages show `/app/file.py` instead of local paths
- Paths don't exist on your local system

**Root Cause**:
Path translation between Docker container and local filesystem

**Debugging Steps**:
1. Check what paths are stored in the database:
```bash
# Connect to Qdrant and query a collection
curl -X POST "http://localhost:6333/collections/claude_template_duplicate_prevention/points/scroll" \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "with_payload": true}' | jq '.result.points[].payload.file_path'
```

2. Verify workspace detection:
```bash
# Check what workspace name is being used
docker logs duplicate-indexer-claude_template-* 2>&1 | grep "Using collection:"
```

3. Check environment variables:
```bash
docker exec duplicate-indexer-claude_template-* env | grep -E "(WORKSPACE|QDRANT)"
```

### Issue 3: Workspace name mismatch

**Symptoms**:
- Guard and indexer using different collection names
- No duplicates detected even when they exist

**Root Cause**:
Inconsistent workspace detection between components

**Solution**:
1. Set explicit workspace name:
```bash
# In docker-compose.yml
environment:
  - WORKSPACE_NAME=claude_template
```

2. Verify both components use same collection:
```bash
# Check indexer
docker logs duplicate-indexer-* | grep "collection:"

# Check guard (trigger a write operation and check logs)
tail -f ~/.claude/logs/adaptive-guard.log | grep "collection"
```

### Issue 4: Vector dimension mismatch

**Symptoms**:
- "Vector dimension mismatch" errors
- Indexing fails after collection creation

**Root Cause**:
Collection created with wrong dimensions

**Solution**:
1. Check current collection dimensions:
```bash
curl http://localhost:6333/collections/your_collection_name | jq '.result.config.params.vectors.size'
```

2. Delete and recreate collection:
```bash
# Stop indexer
./stop-duplicate-indexer.sh

# Remove volumes to wipe database
docker -c default compose down -v

# Restart
./start-duplicate-indexer.sh
```

### Issue 5: No duplicates detected (even when they exist)

**Symptoms**:
- Obviously similar code not being caught
- Guard always returns ALLOW

**Debugging Steps**:

1. Check if vectors are being stored:
```bash
# Query collection statistics
curl http://localhost:6333/collections/your_collection_name | jq '.result.points_count'
```

2. Test similarity threshold:
```python
# Create test script to check similarity scores
python3 -c "
from duplicate_prevention.embedding_generator import EmbeddingGenerator
gen = EmbeddingGenerator()

code1 = 'def hello(): return \"world\"'
code2 = 'def hello(): return \"world\"'  # Identical

emb1 = gen.generate_embedding(code1, 'python')
emb2 = gen.generate_embedding(code2, 'python')

# Calculate cosine similarity
import numpy as np
v1 = np.array(emb1['embedding'])
v2 = np.array(emb2['embedding'])
similarity = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
print(f'Similarity: {similarity}')
"
```

3. Check guard configuration:
```python
# Verify threshold setting
grep "similarity_threshold" ~/.claude/python/guards/duplicate_prevention_guard.py
```

## Logging and Monitoring

### Enable Debug Logging

1. **Indexer Logs**:
```bash
docker logs -f duplicate-indexer-claude_template-* 2>&1
```

2. **Guard Logs**:
```bash
# Enable debug mode in guard
export DUPLICATE_PREVENTION_DEBUG=1

# Watch guard logs
tail -f ~/.claude/logs/adaptive-guard.log
```

3. **Qdrant Logs**:
```bash
docker logs qdrant-duplicate-prevention
```

### Key Log Patterns to Watch

**Successful Indexing**:
```
📄 Indexing: path/to/file.py
✅ Successfully indexed N code files
```

**Path Translation Working**:
```
Converting relative path: file.py -> /home/user/project/file.py
```

**Collection Operations**:
```
Creating collection: workspace_duplicate_prevention
Collection created successfully
```

## Performance Debugging

### Slow Indexing

1. Check for large files:
```bash
find . -name "*.py" -size +1M -exec ls -lh {} \;
```

2. Monitor indexing rate:
```bash
docker logs duplicate-indexer-* 2>&1 | grep -E "Indexing:|indexed" | tail -20
```

3. Check Qdrant performance:
```bash
# Monitor CPU/memory
docker stats qdrant-duplicate-prevention
```

### High Memory Usage

1. Check collection size:
```bash
curl http://localhost:6333/collections | jq '.result.collections[].points_count'
```

2. Monitor container resources:
```bash
docker -c default compose top
```

## Testing and Validation

### Manual Testing

1. **Test duplicate detection**:
```bash
# Create test file
echo "def test(): return 42" > test1.py

# Try to create duplicate
echo "def test(): return 42" > test2.py
# Should be blocked
```

2. **Test self-similarity**:
```bash
# Edit existing file
echo "# Added comment" >> test1.py
# Should be allowed
```

3. **Test path handling**:
```bash
# Check error message shows correct path
# Should see local path, not /app/
```

### Automated Testing

Run the test suite:
```bash
cd duplicate_prevention
pytest tests/ -v
```

## Emergency Procedures

### Complete System Reset

If all else fails:
```bash
# 1. Stop everything
./stop-duplicate-indexer.sh

# 2. Remove all data
docker -c default compose down -v

# 3. Clear any cached data
rm -rf ~/.claude/duplicate_prevention_cache/

# 4. Reinstall hooks
./safe_install.sh

# 5. Start fresh
./start-duplicate-indexer.sh
```

### Disable Temporarily

If blocking critical work:
```bash
# Request override code from operator
HOOK_OVERRIDE_CODE=123456 <your command>
```

## Getting Help

1. Check logs for specific error messages
2. Review this debugging guide
3. Check test plan for expected behaviors
4. Submit issue with:
   - Error messages
   - Steps to reproduce
   - Environment details
   - Log excerpts
