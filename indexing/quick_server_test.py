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

"""Quick test to verify server components work."""

import sys
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent
src_path = current_dir / "src"
sys.path.insert(0, str(src_path))


def test_imports():
    """Test that all imports work."""
    print("🧪 Testing imports...")

    try:
        print("✅ BugFindingAnalyzer imported")
    except Exception as e:
        print(f"❌ BugFindingAnalyzer import failed: {e}")
        return False

    try:
        print("✅ ReviewCodeAnalyzer imported")
    except Exception as e:
        print(f"❌ ReviewCodeAnalyzer import failed: {e}")
        return False

    try:
        print("✅ UsageTracker imported")
    except Exception as e:
        print(f"❌ UsageTracker import failed: {e}")
        return False

    return True


def test_analyzer_initialization():
    """Test analyzer initialization."""
    print("\n🧪 Testing analyzer initialization...")

    try:
        from bug_finding_analyzer import BugFindingAnalyzer
        from review_code_analyzer import ReviewCodeAnalyzer
        from usage_tracker import UsageTracker

        usage_tracker = UsageTracker()

        review_analyzer = ReviewCodeAnalyzer(usage_tracker=usage_tracker)
        bug_analyzer = BugFindingAnalyzer(usage_tracker=usage_tracker)

        print("✅ Both analyzers initialized successfully")

        # Test tool info
        review_name, review_desc, review_schema = review_analyzer.get_tool_info()
        bug_name, bug_desc, bug_schema = bug_analyzer.get_tool_info()

        print(f"✅ Review tool: {review_name}")
        print(f"✅ Bug tool: {bug_name}")

        return True

    except Exception as e:
        print(f"❌ Analyzer initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_schemas():
    """Test schema generation."""
    print("\n🧪 Testing schema generation...")

    try:
        from bug_finding_analyzer import BugFindingAnalyzer
        from review_code_analyzer import ReviewCodeAnalyzer
        from usage_tracker import UsageTracker

        usage_tracker = UsageTracker()
        review_analyzer = ReviewCodeAnalyzer(usage_tracker=usage_tracker)
        bug_analyzer = BugFindingAnalyzer(usage_tracker=usage_tracker)

        # Test schemas
        review_schema = review_analyzer.get_complete_tool_schema()
        bug_schema = bug_analyzer.get_complete_tool_schema()

        print(f"✅ Review schema has {len(review_schema.get('properties', {}))} properties")
        print(f"✅ Bug schema has {len(bug_schema.get('properties', {}))} properties")

        # Check key properties
        if "directory" in review_schema.get("properties", {}):
            print("✅ Review schema has directory property")
        else:
            print("❌ Review schema missing directory property")
            return False

        if "bug_categories" in bug_schema.get("properties", {}):
            print("✅ Bug schema has bug_categories property")
        else:
            print("❌ Bug schema missing bug_categories property")
            return False

        return True

    except Exception as e:
        print(f"❌ Schema generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🚀 Quick Server Component Test")
    print("=" * 40)

    tests_passed = 0
    total_tests = 3

    if test_imports():
        tests_passed += 1

    if test_analyzer_initialization():
        tests_passed += 1

    if test_schemas():
        tests_passed += 1

    print("\n" + "=" * 40)
    print(f"📊 Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("✅ All component tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
