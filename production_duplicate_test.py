def calculate_numbers(number_list):
    """Calculate sum of numbers in a list."""
    sum_total = 0
    for number in number_list:
        sum_total += number
    return sum_total


def compute_average(values):
    """Compute average of values."""
    if not values:
        return 0
    return sum(values) / len(values)
