def calculate_sum(numbers):
    """Calculate the sum of all numbers in a list."""
    total = 0
    for num in numbers:
        total += num
    return total


def find_average(data):
    """Find the average of a list of numbers."""
    if not data:
        return 0
    return sum(data) / len(data)
