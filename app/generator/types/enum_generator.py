"""
Enum type data generation with support for multiple selections.
"""

import random
from typing import Dict, Any, List

def generate_enum(schema: Dict[str, Any]) -> Any:
    """
    Generate a value or a list of values from an enum.

    Supports selecting multiple unique items if min_items or max_items are specified.

    Args:
        schema: The schema dictionary for the enum.
            - "enum" (List): The list of possible values.
            - "min_items" (int, optional): The minimum number of items to select. Defaults to 1.
            - "max_items" (int, optional): The maximum number of items to select. Defaults to 1.
            - "default_items" (int, optional): The default number of items to select if min/max are not set. Defaults to 1.

    Returns:
        A single value from the enum or a list of unique values.
    """
    choices = schema["enum"]
    
    # Determine the number of items to select
    min_items = schema.get("min_items", 1)
    max_items = schema.get("max_items", 1)
    default_items = schema.get("default_items")

    # If default_items is specified and min/max are at their default, use default_items
    if default_items is not None and min_items == 1 and max_items == 1:
        k = default_items
    else:
        # Ensure max_items is not less than min_items
        actual_max = max(min_items, max_items)
        k = random.randint(min_items, actual_max)

    # Ensure we don't try to select more items than available
    k = min(k, len(choices))

    if k == 1:
        # If only one item is to be selected, return it directly (maintains original behavior)
        return random.choice(choices)
    else:
        # If multiple items are to be selected, return a list of unique samples
        return random.sample(choices, k)
