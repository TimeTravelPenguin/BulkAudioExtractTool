from more_itertools import consecutive_groups


def find_missing(lst):
    # src: https://www.geeksforgeeks.org/python-find-missing-numbers-in-a-sorted-list-range/
    return sorted(set(range(lst[0], lst[-1])) - set(lst))


def pretty_range(*nums: int):
    ranges = consecutive_groups(nums)

    outputs = []
    for nums in ranges:
        nums = list(nums)

        if len(nums) == 1:
            outputs.append(str(nums[0]))
            continue

        outputs.append(f"{min(nums)}-{max(nums)}")
    return ", ".join(outputs)
