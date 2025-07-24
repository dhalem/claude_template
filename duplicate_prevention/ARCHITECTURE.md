# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

# Duplicate Prevention System Architecture

## Overview

The Duplicate Prevention System is a sophisticated code similarity detection system that prevents developers from accidentally creating duplicate code. It uses semantic embeddings to understand code meaning beyond simple text matching, and integrates seamlessly with Claude Code through the hook system.

## System Components

### 1. Core Components

```
duplicate_prevention/
├── database.py              # Qdrant database connector
├── embedding_generator.py   # Code to vector embeddings
├── workspace_detector.py    # Workspace boundary detection
├── config.py               # Configuration management
└── watch_and_index.py      # Continuous indexing service
```

### 2. Integration Components

```
hooks/python/guards/
└── duplicate_prevention_guard.py  # Claude Code hook guard

scripts/
└── index_repository.py           # Repository indexing script
```

### 3. Infrastructure Components

```
duplicate_prevention/
├── docker-compose.yml      # Container orchestration
├── Dockerfile             # Indexer container definition
├── requirements.txt       # Python dependencies
├── start-duplicate-indexer.sh
└── stop-duplicate-indexer.sh
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code Editor                        │
├─────────────────────────────────────────────────────────────────┤
│                          Hook System                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          DuplicatePreventionGuard (Python)              │   │
│  │  - Intercepts Write/Edit operations                     │   │
│  │  - Generates embeddings for new code                    │   │
│  │  - Queries Qdrant for similar code                      │   │
│  │  - Blocks or allows based on similarity                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Query/Store
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Qdrant Vector Database                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Workspace-Specific Collections                   │   │
│  │  - project1_duplicate_prevention                        │   │
│  │  - project2_duplicate_prevention                        │   │
│  │  - Each stores code embeddings with metadata            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ Index
                                  │
┌─────────────────────────────────────────────────────────────────┐
│              Docker: Continuous Indexing Service                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Watch and Index Service                     │   │
│  │  - Monitors /workspace for changes                       │   │
│  │  - Generates embeddings for code files                  │   │
│  │  - Stores in Qdrant with relative paths                 │   │
│  │  - Handles create/update/delete events                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Indexing Flow (Docker Container)

```
File Change Event → Watchdog → Index Repository
                                      ↓
                              Extract Code Units
                                      ↓
                              Generate Embeddings
                                      ↓
                              Store in Qdrant
                              (with relative paths)
```

### 2. Duplicate Detection Flow (Hook)

```
User Writes Code → Hook Intercepts → Extract Content
                                           ↓
                                    Generate Embedding
                                           ↓
                                    Query Similar Vectors
                                           ↓
                                    Convert Paths (relative → absolute)
                                           ↓
                                    Check Self-Similarity
                                           ↓
                                    Block/Allow Decision
```

## Key Design Decisions

### 1. Workspace Isolation

Each project/workspace has its own Qdrant collection to prevent cross-project contamination:

```python
# Collection naming: {workspace_name}_duplicate_prevention
"claude_template_duplicate_prevention"
"my_project_duplicate_prevention"
```

### 2. Path Handling Strategy

**Problem**: Docker containers see different paths than local development
**Solution**: Three-layer path handling

1. **Storage Layer**: Store relative paths in Qdrant
   ```python
   metadata = {
       "file_path": "src/utils/helper.py",  # Relative path
       "function_name": "process_data"
   }
   ```

2. **Indexing Layer**: Convert absolute container paths to relative
   ```python
   # /workspace/src/utils/helper.py → src/utils/helper.py
   relative_path = file_path.relative_to(workspace_root)
   ```

3. **Display Layer**: Convert relative paths back to absolute local paths
   ```python
   # src/utils/helper.py → /home/user/project/src/utils/helper.py
   local_path = Path(workspace_root) / relative_path
   ```

### 3. Self-Similarity Handling

Prevents blocking edits to the same file:

```python
# Compare paths after normalization
if result_file_path == current_file_path:
    continue  # Don't block edits to same file
```

### 4. Embedding Strategy

Uses sentence-transformers for semantic understanding:

- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Preprocessing**: Language-aware code cleaning
- **Chunking**: Function/class extraction with fallback to fixed-size chunks

### 5. Docker Architecture

**Separation of Concerns**:
- Indexer code at `/indexer` (immutable)
- Workspace mounted at `/workspace` (read-only)
- No mixing of application and data

## Configuration

### Environment Variables

```bash
# Docker Container
WORKSPACE_NAME=claude_template    # Override workspace detection
QDRANT_HOST=qdrant               # Qdrant service name in Docker
WORKSPACE_PATH=/path/to/project  # Local path to mount

# Guard
DUPLICATE_PREVENTION_DEBUG=1     # Enable debug logging
SIMILARITY_THRESHOLD=0.70        # Similarity threshold (0-1)
```

### Collection Configuration

```python
{
    "vector_size": 384,           # Must match embedding model
    "distance": "Cosine",         # Similarity metric
    "on_disk": False              # In-memory for performance
}
```

## Operational Aspects

### 1. Multi-Instance Support

The system supports multiple projects on the same machine:

```bash
# Project paths are hashed to create unique names
PROJECT_HASH=$(echo "$PROJECT_DIR" | sha256sum | cut -c1-8)
COMPOSE_PROJECT_NAME="${PROJECT_NAME}-${PROJECT_HASH}"
```

### 2. Health Monitoring

- Indexer health: `http://localhost:{port}/health`
- Qdrant health: `http://localhost:6333/health`
- Container logs: `docker logs duplicate-indexer-*`

### 3. Performance Considerations

- **Initial Indexing**: Can take 2-5 minutes for large repos
- **Incremental Updates**: Near real-time (< 1 second)
- **Query Performance**: < 100ms for similarity search
- **Memory Usage**: ~500MB for 10,000 code files

## Security Considerations

1. **Read-Only Mounts**: Workspace mounted read-only in Docker
2. **Network Isolation**: Containers on isolated network
3. **No External Access**: Qdrant not exposed publicly
4. **Input Validation**: All paths sanitized before use

## Extension Points

### 1. Custom Embedding Models

```python
class CustomEmbeddingModel(EmbeddingModel):
    def load_model(self):
        # Load your model

    def generate_embedding(self, text: str):
        # Return embedding vector
```

### 2. Alternative Vector Databases

The `DatabaseConnector` interface can be implemented for other databases:

```python
class PineconeConnector(DatabaseConnector):
    def create_collection(self, name: str, vector_size: int):
        # Pinecone-specific implementation
```

### 3. Language-Specific Preprocessing

Add new language processors in `embedding_generator.py`:

```python
def preprocess_rust(self, code: str) -> str:
    # Rust-specific preprocessing
```

## Troubleshooting Integration

See `DEBUGGING_GUIDE.md` for:
- Common issues and solutions
- Log analysis techniques
- Performance debugging
- Emergency procedures

## Future Enhancements

1. **Semantic Clustering**: Group similar code patterns
2. **Refactoring Suggestions**: Recommend code consolidation
3. **Cross-Language Detection**: Find similar patterns across languages
4. **IDE Integration**: Direct VSCode/IntelliJ plugins
5. **Team Analytics**: Dashboard for duplicate code metrics
