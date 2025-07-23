import re

# Simulate the exact normalization process
js_code = '''
function calculateSum(a, b) {
    // This is a comment
    /* Multi-line
       comment */
    const result = a + b; // inline comment
    return result;
}
'''

print('Step by step normalization:')
print('1. Original:')
print(repr(js_code))

# Step 1: strip
normalized = js_code.strip()
print('\n2. After strip():')
print(repr(normalized))

# Step 2: Remove comments
patterns = [r'//.*$', r'/\*[\s\S]*?\*/']
for i, pattern in enumerate(patterns):
    print(f'\n3.{i+1}. After removing pattern {pattern}:')
    if 'python' == 'javascript' and pattern.startswith(r'#'):
        normalized = re.sub(pattern, '', normalized, flags=re.MULTILINE)
    else:
        normalized = re.sub(pattern, '', normalized, flags=re.MULTILINE | re.DOTALL)
    print(repr(normalized))

# Step 3: Clean up extra whitespace
print('\n4. Before whitespace cleanup:')
print(repr(normalized))
normalized = re.sub(r'\n\s*\n\s*\n', '\n\n', normalized)
print('\n5. After reducing multiple blank lines:')
print(repr(normalized))
normalized = normalized.strip()
print('\n6. Final result after strip():')
print(repr(normalized))
