def calculate_sum(numbers):
    """Calculate the sum of all numbers in a list.

    This function takes a list of numbers and returns their total sum.
    It iterates through each number and adds them together.

    Args:
        numbers: A list of numeric values

    Returns:
        The sum of all numbers in the list
    """
    total = 0
    for number in numbers:
        total += number
    return total
