import re

js_code = '''
function calculateSum(a, b) {
    // This is a comment
    /* Multi-line
       comment */
    const result = a + b; // inline comment
    return result;
}
'''

print('Original:')
print(repr(js_code))
print()

# Remove single-line comments first
after_single = re.sub(r'//.*$', '', js_code, flags=re.MULTILINE)
print('After removing // comments:')
print(repr(after_single))
print()

# Test different multi-line comment patterns
patterns = [
    r'/\*[\s\S]*?\*/',  # Original pattern
    r'/\*.*?\*/',       # New pattern (doesn't work with newlines)
    r'/\*[^*]*\*+([^/*][^*]*\*+)*/',  # More complex pattern
]

for i, pattern in enumerate(patterns, 1):
    try:
        result = re.sub(pattern, '', after_single, flags=re.MULTILINE | re.DOTALL)
        print(f'Pattern {i} ({pattern}):')
        print(repr(result))
        print()
    except Exception as e:
        print(f'Pattern {i} failed: {e}')
        print()
