"""This class is used to access and modify the study configuration."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules

# Import third-party modules
from typing import Any

import ruamel.yaml

# Import user-defined modules


# ==================================================================================================
# --- Function definition
# ==================================================================================================


def load_configuration_from_path(
    path: str, ryaml: ruamel.yaml.YAML | None = None
) -> tuple[dict, ruamel.yaml.YAML]:
    if ryaml is None:
        # Initialize yaml reader
        ryaml = ruamel.yaml.YAML()

    # Load configuration
    with open(path, "r") as fid:
        configuration = ryaml.load(fid)

    return configuration, ryaml


def write_configuration_to_path(
    configuration: dict, path: str, ryaml: ruamel.yaml.YAML | None = None
) -> None:
    if ryaml is None:
        # Initialize yaml reader
        ryaml = ruamel.yaml.YAML()

    # Write configuration
    with open(path, "w") as fid:
        ryaml.dump(configuration, fid)


def nested_get(dic, keys):
    # Adapted from https://stackoverflow.com/questions/14692690/access-nested-dictionary-items-via-a-list-of-keys
    """Get the value from a nested dictionary using a list of keys.

    Args:
        dic (dict): The nested dictionary.
        keys (list): The list of keys to traverse the nested dictionary.

    Returns:
        Any: The value corresponding to the keys in the nested dictionary.

    """
    for key in keys:
        dic = dic[key]
    return dic


def nested_set(dic, keys, value):
    """Set a value in a nested dictionary using a list of keys.

    Args:
        dic (dict): The nested dictionary.
        keys (list): The list of keys to traverse the nested dictionary.
        value (Any): The value to set in the nested dictionary.

    Returns:
        None

    """
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def find_item_in_dict(obj: dict, key: str) -> Any:
    """Find an item in a nested dictionary.

    Args:
        obj (dict): The nested dictionary.
        key (str): The key to find in the nested dictionary.

    Returns:
        Any: The value corresponding to the key in the nested dictionary.

    """
    if key in obj:
        return obj[key]
    for v in obj.values():
        if isinstance(v, dict):
            item = find_item_in_dict(v, key)
            if item is not None:
                return item


def set_item_in_dict(obj: dict, key: str, value: Any, found: bool = False):
    """Set an item in a nested dictionary.

    Args:
        obj (dict): The nested dictionary.
        key (str): The key to set in the nested dictionary.
        value (Any): The value to set in the nested dictionary.
        found (bool): Whether the key has been found in the nested dictionary.

    Returns:
        None

    """
    if key in obj:
        if found:
            raise ValueError(f"Key {key} found more than once in the nested dictionary.")

        obj[key] = value
        found = True
    for v in obj.values():
        if isinstance(v, dict):
            set_item_in_dict(v, key, value, found)
