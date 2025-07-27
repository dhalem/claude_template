# A1.6: Workspace-Specific Duplicate Prevention System

## Problem Statement

The current duplicate prevention system uses a single shared Qdrant database collection for all workspaces, which causes:

- **Cross-workspace pollution**: Code from different projects interferes with duplicate detection
- **False positives**: Similar code from unrelated projects triggers duplicate warnings
- **Privacy concerns**: Code from private projects visible to other workspaces
- **Inconsistent behavior**: Different workspaces see different duplicate detection results

## Solution Overview

Transform duplicate prevention to work per-workspace, following the same pattern as the code search indexer:

- **Workspace isolation**: Each workspace gets its own duplicate prevention scope
- **Automatic detection**: System detects current workspace like code search does
- **Collection naming**: Generate unique collection names based on workspace path
- **Independent operation**: Each workspace operates independently

## User Experience

### Current Problematic Experience
1. Developer works on Project A, creates function `calculateTotal()`
2. Developer switches to Project B, creates similar function
3. System warns about duplication from unrelated Project A
4. Developer confused - why does Project B care about Project A code?

### Improved Experience
1. Developer works on Project A, creates function `calculateTotal()`
2. System indexes this in "project_a_duplicates" collection
3. Developer switches to Project B, creates similar function
4. System checks only "project_b_duplicates" collection
5. No false warnings from unrelated projects

## Implementation Strategy

### Phase 1: Workspace Detection
- **Workspace root discovery**: Find workspace boundary like code search indexer
- **Collection name generation**: Create unique names from workspace path
- **Workspace fingerprinting**: Ensure consistent naming across sessions

### Phase 2: Collection Management
- **Auto-creation**: Create workspace collections on first use
- **Migration strategy**: Handle existing shared collections
- **Cleanup protocols**: Remove unused workspace collections

### Phase 3: Guard Integration
- **Dynamic collection naming**: Update DuplicatePreventionGuard to use workspace collections
- **Backward compatibility**: Handle systems without workspace detection
- **Error handling**: Graceful fallback when workspace detection fails

### Phase 4: Testing and Validation
- **Multi-workspace testing**: Verify isolation between workspaces
- **Cross-session consistency**: Same workspace always uses same collection
- **Performance verification**: Ensure workspace detection doesn't slow system

## Technical Architecture

### Workspace Detection Logic
Follow the same pattern as code search indexer:
- Start from current working directory
- Search for workspace indicators (git root, package files, etc.)
- Generate stable workspace identifier
- Use identifier for collection naming

### Collection Naming Convention
- **Format**: `{workspace_name}_duplicate_prevention`
- **Sanitization**: Remove special characters, normalize paths
- **Uniqueness**: Ensure different workspaces get different names
- **Stability**: Same workspace always generates same name

### Database Schema
- **Per-workspace collections**: Each workspace gets dedicated Qdrant collection
- **Shared database**: Continue using single Qdrant instance
- **Collection metadata**: Track workspace association for debugging
- **Migration path**: Move existing vectors to appropriate workspace collections

## Benefits

### For Developers
- **Relevant results**: Only see duplicates from current project
- **Faster detection**: Smaller collections mean faster searches
- **Privacy protection**: Code stays within workspace boundaries
- **Cleaner workflow**: No confusion from unrelated projects

### For System
- **Scalability**: Collections grow with individual projects, not combined
- **Maintainability**: Clear ownership of collections by workspace
- **Debugging**: Easy to identify which workspace owns which data
- **Resource efficiency**: Only search relevant subset of code

## Success Criteria

### Functional Requirements
- **Workspace isolation**: Code from different workspaces never cross-reference
- **Automatic operation**: No manual configuration required per workspace
- **Consistent naming**: Same workspace always uses same collection name
- **Graceful fallback**: System works even if workspace detection fails

### Performance Requirements
- **Fast workspace detection**: Under 100ms to identify workspace
- **Efficient searching**: Similar performance to current system
- **Memory efficiency**: No excessive memory usage from workspace logic
- **Startup speed**: No significant delay in guard initialization

### User Experience Requirements
- **Transparent operation**: Users don't need to know about workspace logic
- **Accurate results**: Only relevant duplicates from current workspace
- **Clear messaging**: If duplicate found, show which file in current workspace
- **No false positives**: Never warn about code from different workspaces

## Implementation Timeline

### Week 1: Foundation
- Workspace detection implementation
- Collection naming logic
- Basic testing framework

### Week 2: Integration
- DuplicatePreventionGuard updates
- Database collection management
- Error handling and fallback

### Week 3: Testing
- Multi-workspace test scenarios
- Cross-session consistency verification
- Performance benchmarking

### Week 4: Migration
- Existing data migration strategy
- Production deployment
- Documentation and training

## Risk Mitigation

### Technical Risks
- **Workspace detection failure**: Fallback to global collection
- **Collection naming conflicts**: Add randomization if needed
- **Performance degradation**: Optimize workspace detection logic
- **Database errors**: Graceful error handling and logging

### User Experience Risks
- **Confusion about scope**: Clear documentation about workspace boundaries
- **Lost duplicates**: Migration strategy preserves existing data
- **Inconsistent behavior**: Extensive testing across workspace types
- **Setup complexity**: Fully automatic operation, no manual steps

## Future Enhancements

### Advanced Features
- **Cross-workspace search**: Optional mode to search all workspaces
- **Workspace hierarchies**: Support for nested workspace structures
- **Collection sharing**: Allow specific workspaces to share collections
- **Analytics dashboard**: Track duplicate patterns across workspaces

### Integration Opportunities
- **IDE integration**: Workspace detection from editor context
- **CI/CD integration**: Duplicate checking in build pipelines
- **Team collaboration**: Shared workspace collections for team projects
- **Code review integration**: Duplicate detection in pull requests

---

**Document Status**: Planning Complete
**Next Phase**: Implementation with TodoWrite tracking
**Owner**: AI Assistant
**Stakeholders**: Development Team, Claude Code Users
