def sum_all_numbers(number_list):
    """Sum all numbers in the provided list.

    This function takes a list of numbers and calculates their total
    by iterating through each element and adding it to a running sum.

    Args:
        number_list: A list containing numeric values

    Returns:
        The total sum of all numbers in the list
    """
    total = 0
    for num in number_list:
        total += num
    return total
