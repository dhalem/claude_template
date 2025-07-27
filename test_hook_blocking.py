def test_duplicate_function():
    """Test function that might be similar to existing code."""
    result = 0
    for item in [1, 2, 3, 4, 5]:
        result += item
    return result
