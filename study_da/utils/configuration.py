"""This class provide various functions to manipulate dictionaries (e.g. configuration)."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
from typing import Any

# Import third-party modules
import numpy as np
import ruamel.yaml

# Import user-defined modules


# ==================================================================================================
# --- Function definition
# ==================================================================================================


def load_dic_from_path(
    path: str, ryaml: ruamel.yaml.YAML | None = None
) -> tuple[dict, ruamel.yaml.YAML]:
    """Load a dictionary from a yaml file.

    Args:
        path (str): The path to the yaml file.
        ryaml (ruamel.yaml.YAML): The yaml reader.

    Returns:
        tuple[dict, ruamel.yaml.YAML]: The dictionary and the yaml reader.

    """

    if ryaml is None:
        # Initialize yaml reader
        ryaml = ruamel.yaml.YAML()

    # Load dic
    with open(path, "r") as fid:
        dic = ryaml.load(fid)

    return dic, ryaml


def write_dic_to_path(dic: dict, path: str, ryaml: ruamel.yaml.YAML | None = None) -> None:
    """Write a dictionary to a yaml file.

    Args:
        dic (dict): The dictionary to write.
        path (str): The path to the yaml file.
        ryaml (ruamel.yaml.YAML): The yaml reader.

    Returns:
        None

    """

    if ryaml is None:
        # Initialize yaml reader
        ryaml = ruamel.yaml.YAML()

    # Write dic
    with open(path, "w") as fid:
        ryaml.dump(dic, fid)


def nested_get(dic: dict, keys: list) -> Any:
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


def nested_set(dic: dict, keys: list, value: Any) -> None:
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


def set_item_in_dict(obj: dict, key: str, value: Any, found: bool = False) -> None:
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


# This function can probably be made more robust
def clean_dict(o: Any) -> None:
    """Convert numpy types to standard types in a nested dictionary containing number and lists.

    Args:
        o (Any): The object to convert.

    Returns:
        None
    """
    if not isinstance(o, dict):
        return
    for k, v in o.items():
        if isinstance(v, np.generic):
            o[k] = v.item()
        elif isinstance(v, list):
            for i, x in enumerate(v):
                if isinstance(x, np.generic):
                    v[i] = x.item()
                if isinstance(x, dict):
                    clean_dict(x)
        else:
            clean_dict(v)
