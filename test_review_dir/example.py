# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm


def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total


def find_max(items):
    if not items:
        return None

    max_val = items[0]
    for i in range(1, len(items)):
        if items[i] > max_val:
            max_val = items[i]
    return max_val


class Calculator:
    def __init__(self):
        self.result = 0

    def add(self, x, y):
        return x + y

    def multiply(self, x, y):
        result = 0
        for i in range(y):
            result = result + x
        return result

    def divide(self, x, y):
        if y == 0:
            raise ValueError("Division by zero")
        return x / y
