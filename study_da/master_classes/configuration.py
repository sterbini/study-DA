"""This class is used to access and modify the study configuration."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules

# Import third-party modules
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
