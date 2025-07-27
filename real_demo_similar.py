def calculate_total(data):
    """Calculate the total of all numbers in the data.

    This function processes a list of numbers and computes their sum
    by going through each value and adding it to an accumulator.

    Args:
        data: A list containing numeric values to sum

    Returns:
        The calculated sum of all numbers
    """
    result = 0
    for value in data:
        result += value
    return result
