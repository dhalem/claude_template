def calculate_sum(numbers):
    """Calculate the sum of numbers in a list."""
    total = 0
    for num in numbers:
        total += num
    return total


def multiply_values(data_list):
    """Multiply all values in the data list."""
    result = 1
    for value in data_list:
        result *= value
    return result
