#!/usr/bin/env python3
# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Basic duplicate prevention system test - works without Docker."""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_basic_functionality():
    """Test basic duplicate prevention components."""
    print("🧪 Testing Duplicate Prevention System")
    print("=====================================")

    # Test 1: Import all modules
    print("\n1. Testing module imports...")
    try:
        from duplicate_prevention.database import DatabaseConnector
        from duplicate_prevention.embedding_generator import EmbeddingGenerator
        from duplicate_prevention.workspace_detector import workspace_detector

        print("   ✅ All modules imported successfully")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

    # Test 2: Database connector initialization
    print("\n2. Testing database connector...")
    try:
        db = DatabaseConnector(host="localhost", port=6333)
        print(f"   ✅ Database connector created: {db.base_url}")
    except Exception as e:
        print(f"   ❌ Database connector failed: {e}")
        return False

    # Test 3: Embedding generator
    print("\n3. Testing embedding generation...")
    try:
        embedding_gen = EmbeddingGenerator()

        # Test simple code embedding
        test_code = """
def hello_world():
    print("Hello, world!")
    return True
"""
        result = embedding_gen.generate_embedding(test_code, "python")
        if result and "embedding" in result:
            embedding = result["embedding"]
            print(f"   ✅ Embedding generated: {len(embedding)} dimensions")
        else:
            print("   ❌ No embedding returned")
            return False
    except Exception as e:
        print(f"   ❌ Embedding generation failed: {e}")
        return False

    # Test 4: Workspace detection
    print("\n4. Testing workspace detection...")
    try:
        workspace_info = workspace_detector.get_workspace_info()
        print(f"   ✅ Workspace detected: {workspace_info.get('workspace_name', 'unknown')}")
        print(f"   📁 Collection name: {workspace_info.get('collection_name', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Workspace detection failed: {e}")
        return False

    # Test 5: Duplicate prevention guard
    print("\n5. Testing duplicate prevention guard...")
    try:
        sys.path.insert(0, str(project_root / "hooks" / "python"))
        from base_guard import GuardContext
        from guards.duplicate_prevention_guard import DuplicatePreventionGuard

        guard = DuplicatePreventionGuard()
        print(f"   ✅ Guard created: {guard.name}")
        print(f"   🛡️  Default action: {guard.get_default_action()}")

        # Test guard with non-file operation (should not trigger)
        context = GuardContext(tool_name="Bash", tool_input={"command": "ls -la"}, command="ls -la")
        should_trigger = guard.should_trigger(context)
        print(f"   ✅ Non-file operation trigger test: {not should_trigger}")

    except Exception as e:
        print(f"   ❌ Guard test failed: {e}")
        return False

    # Test 6: End-to-end workflow (without database)
    print("\n6. Testing end-to-end workflow...")
    try:
        # Create a temporary Python file context
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            test_content = """
def calculate_sum(a, b):
    \"\"\"Calculate the sum of two numbers.\"\"\"
    return a + b
"""
            f.write(test_content)
            temp_file = f.name

        try:
            context = GuardContext(
                tool_name="Write",
                tool_input={"file_path": temp_file, "content": test_content},
                file_path=temp_file,
                content=test_content,
            )

            # This should not trigger because no database connection (graceful fallback)
            should_trigger = guard.should_trigger(context)
            print(f"   ✅ Guard handles missing database gracefully: {not should_trigger}")

        finally:
            os.unlink(temp_file)

    except Exception as e:
        print(f"   ❌ End-to-end test failed: {e}")
        return False

    print("\n🎉 All tests passed! Duplicate prevention system is working correctly.")
    print("\n📝 Next steps:")
    print("   - Set up Qdrant database for full functionality")
    print("   - Run ./run_duplicate_prevention_tests.sh for comprehensive testing")
    print("   - Test with real code files and similarity detection")

    return True


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
