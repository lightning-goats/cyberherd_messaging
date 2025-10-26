# utils.py - helper functions for CyberHerd Messaging
import random
from .defaults import GOAT_NAMES_DICT


def get_random_goat_names(goat_names_dict: dict = GOAT_NAMES_DICT):
    """Select random goat names from the dictionary."""
    keys = list(goat_names_dict.keys())
    selected_keys = random.sample(keys, random.randint(1, len(keys)))
    return [(key, goat_names_dict[key][0], goat_names_dict[key][1]) for key in selected_keys]


def join_with_and(items: list[str]) -> str:
    """Join list of strings with commas and 'and'."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]
