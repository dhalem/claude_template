def calculate_sum_of_numbers(input_data):
    """Calculate the sum of all numbers in the input data list.

    This function iterates through a list of numbers and adds them up.
    It returns the total sum of all the numbers.

    Args:
        input_data: A list of numbers to sum up

    Returns:
        The total sum as an integer or float
    """
    running_total = 0

    # Iterate through each number in the input
    for current_number in input_data:
        # Add the current number to our running total
        running_total += current_number

    # Return the final calculated sum
    return running_total
