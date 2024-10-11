"""This is a template script for generation 1 of simulation study, in which ones generates a
particle distribution and a collider from a MAD-X model."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import time

import numpy as np

# Import third-party modules
# Import user-defined modules
from study_da.utils import (
    load_dic_from_path,
    set_item_in_dict,
    write_dic_to_path,
)

# Set up the logger here if needed


# ==================================================================================================
# --- Script functions
# ==================================================================================================
def add(configuration):
    b = float(configuration["a_random_nest"]["b"])
    x2_plus_z2 = float(configuration["result"]["x2_plus_z2"])
    configuration["result"] = {"x_plus_z_3": x2_plus_z2 * b}
    return configuration


# ==================================================================================================
# --- Parameters definition
# ==================================================================================================
dict_mutated_parameters = {{parameters}}
path_configuration = "{{main_configuration}}"

# ==================================================================================================
# --- Script for execution
# ==================================================================================================

if __name__ == "__main__":
    logging.info("Starting custom script")

    # Load full configuration
    full_configuration, ryaml = load_dic_from_path(path_configuration)

    # Mutate parameters in configuration
    for key, value in dict_mutated_parameters.items():
        set_item_in_dict(full_configuration, key, value)

    # Add x and z and write to configuration
    full_configuration = add(full_configuration)

    # Dump configuration
    write_dic_to_path(full_configuration, path_configuration.split("/")[-1], ryaml)

    logging.info("Script finished")
