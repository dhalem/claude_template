# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Duplicate Prevention System

A sophisticated semantic code similarity detection system that prevents developers from accidentally creating duplicate code. Uses AI-powered embeddings to understand code meaning beyond simple text matching.

## 🚀 Quick Start

```bash
# 1. Start the duplicate prevention system
./start-duplicate-indexer.sh

# 2. Wait for initial indexing (check logs)
docker logs -f duplicate-indexer-claude_template-*

# 3. System is now active - try creating duplicate code!
```

## 📚 Documentation

- **[Architecture Guide](ARCHITECTURE.md)** - Complete system design and components
- **[Debugging Guide](DEBUGGING_GUIDE.md)** - Troubleshooting common issues
- **[Test Plan](DUPLICATE_PREVENTION_TEST_PLAN.md)** - Comprehensive testing strategy
- **[Development Guide](DEVELOPMENT_GUIDE.md)** - TDD process and implementation details

## 🎯 Key Features

- **Semantic Understanding**: Uses AI embeddings to detect similar code even with different variable names
- **Workspace Isolation**: Each project has its own similarity database
- **Self-Similarity Handling**: Allows editing existing files without false positives
- **Docker-Based Indexing**: Continuous monitoring and indexing of code changes
- **Path Translation**: Seamless handling of Docker vs local filesystem paths
- **Claude Code Integration**: Works automatically through the hook system

## 🏗️ System Architecture

```
Claude Code → Hook System → Duplicate Prevention Guard
                                    ↓
                            Generate Embedding
                                    ↓
                            Query Qdrant Database
                                    ↓
                            Block/Allow Decision
```

## 🔧 How It Works

1. **Continuous Indexing**: Docker container monitors your codebase and indexes all code files
2. **Embedding Generation**: Code is converted to semantic vectors using sentence-transformers
3. **Similarity Search**: When you write new code, it's compared against the indexed codebase
4. **Smart Blocking**: Blocks creation of duplicate code while allowing edits to existing files
5. **Clear Feedback**: Shows exactly where similar code exists with similarity scores

## 📋 Requirements

- Docker and Docker Compose
- Python 3.11+
- Claude Code with hook system installed
- ~500MB RAM for vector database

## 🛠️ Installation

The duplicate prevention system is installed automatically by `safe_install.sh`:

```bash
# From project root
./safe_install.sh
```

To start the indexing service:

```bash
cd duplicate_prevention
./start-duplicate-indexer.sh
```

## 🔍 Common Issues

### "Similar code already exists" when editing same file
- **Solution**: System now handles self-similarity - update hooks with `./safe_install.sh`

### Docker paths in error messages
- **Solution**: Path translation is implemented - ensure you have the latest version

### Workspace name mismatch
- **Solution**: Set `WORKSPACE_NAME` environment variable in docker-compose.yml

See [Debugging Guide](DEBUGGING_GUIDE.md) for detailed troubleshooting.

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd duplicate_prevention
pytest tests/ -v
```

See [Test Plan](DUPLICATE_PREVENTION_TEST_PLAN.md) for testing strategy.

## ⚙️ Configuration

### Environment Variables

```bash
# For Docker container
WORKSPACE_NAME=my_project       # Override automatic detection
WORKSPACE_PATH=/path/to/project # Local project path
QDRANT_HOST=qdrant             # Qdrant hostname (Docker)

# For guard
SIMILARITY_THRESHOLD=0.70       # Similarity threshold (0-1)
DUPLICATE_PREVENTION_DEBUG=1    # Enable debug logging
```

### Similarity Threshold

- **0.70** (default): Good balance of catching duplicates without false positives
- **0.80**: More strict - only very similar code blocked
- **0.60**: More lenient - catches more potential duplicates

## 📊 Performance

- **Initial Indexing**: 2-5 minutes for large repositories
- **Incremental Updates**: < 1 second per file change
- **Query Time**: < 100ms for similarity search
- **Memory Usage**: ~500MB for 10,000 files

## 🚨 Emergency Procedures

### Disable Temporarily
```bash
# Use override code from operator
HOOK_OVERRIDE_CODE=123456 <your command>
```

### Complete Reset
```bash
./stop-duplicate-indexer.sh
docker -c default compose down -v
./start-duplicate-indexer.sh
```

## 🤝 Contributing

1. Read [Architecture Guide](ARCHITECTURE.md) first
2. Follow TDD process in [Development Guide](DEVELOPMENT_GUIDE.md)
3. Ensure all tests pass
4. Update documentation as needed

## 📝 License

Part of the Claude Template project. See main project LICENSE.
