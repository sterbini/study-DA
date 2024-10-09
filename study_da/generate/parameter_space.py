"""This module is used to handle parameter space generation from e.g. linspace, logspace, lists, etc."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
from typing import Any

# Import third-party modules
import numpy as np

# Import user-defined modules
from study_da.utils import find_item_in_dict

# ==================================================================================================
# --- Functions
# ==================================================================================================


def convert_for_subvariables(l_subvariables: list[str], parameter_list: list) -> list:
    """Convert the parameter list to a list of dictionaries with subvariables as keys.

    Args:
        subvariables (list[str]): List of subvariables.
        parameter_list (list): List with the parameter values.

    Returns:
        list: List of dictionaries with subvariables as keys.
    """
    return [{subvar: value for subvar in l_subvariables} for value in parameter_list]


def linspace(l_values_linspace: list) -> np.ndarray:
    """Generate a list of evenly spaced values over a specified interval.

    Args:
        l_values_linspace (list): List with the values for the linspace function.

    Returns:
        np.ndarray: List of evenly spaced values."""

    # Check that all values in the list are floats or integers
    if not all(isinstance(value, (float, int)) for value in l_values_linspace):
        raise ValueError(
            "All values in the list for the linspace function must be floats or integers."
        )
    return np.round(
        np.linspace(
            l_values_linspace[0],
            l_values_linspace[1],
            l_values_linspace[2],
            endpoint=True,
        ),
        5,
    )


def logspace(l_values_logspace: list) -> np.ndarray:
    """Generate a list of values that are evenly spaced on a log scale.

    Args:
        l_values_logspace (list): List with the values for the logspace function.

    Returns:
        np.ndarray: List of values that are evenly spaced on a log scale.
    """

    # Check that all values in the list are floats or integers
    if not all(isinstance(value, (float, int)) for value in l_values_logspace):
        raise ValueError(
            "All values in the list for the logspace function must be floats or integers."
        )
    return np.round(
        np.logspace(
            l_values_logspace[0],
            l_values_logspace[1],
            l_values_logspace[2],
            endpoint=True,
        ),
        5,
    )


def list_values_path(
    l_values_path_list: list[str], dic_common_parameters: dict[str, Any]
) -> list[str]:
    """Generate a list of path names from an inital path name.

    Args:
        l_values_path_list (list): List with the initial path names and number of paths.
        dic_common_parameters (dict): Dictionary with the parameters common to the whole study.

    Returns:
        list: List of final path values from the initial paths.
    """
    # Check that all values in the list are strings
    if not all(isinstance(value, str) for value in l_values_path_list):
        raise ValueError(
            "All values in the list for the list_values_path function must be strings."
        )
    n_path_arg = l_values_path_list[1]
    n_path = find_item_in_dict(dic_common_parameters, n_path_arg)
    if n_path is None:
        raise ValueError(f"Parameter {n_path_arg} is not defined in the scan configuration.")
    return [l_values_path_list[0].replace("____", f"{n:02d}") for n in range(n_path)]
